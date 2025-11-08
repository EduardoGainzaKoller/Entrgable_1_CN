#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script: deploy_champions_serverless.py
Descripción: Despliega la infraestructura serverless de Champions en AWS con imágenes Lambda Docker,
             reutilizando el mismo ECR y DynamoDB que ECS.
"""

import boto3
import subprocess
import os
import sys

REGION = "us-east-1"

TEMPLATES = {
    "DynamoDB": "dynamodb.yaml",
    "App": "main-lambda.yaml"
}

LAMBDA_FOLDERS = [
    {"name": "createchampion", "path": "lambdas/createChampion"},
    {"name": "getchampionbyid", "path": "lambdas/getChampionById"},
    {"name": "getchampions", "path": "lambdas/getChampions"},
    {"name": "updatechampion", "path": "lambdas/updateChampions"},
    {"name": "deletechampion", "path": "lambdas/deleteChampion"}
]

cf = boto3.client("cloudformation", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)


def run_command(cmd, cwd=None):
    print(f"🛠️ Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def deploy_stack(stack_name, template_file, parameters=None):
    try:
        with open(template_file, "r") as f:
            template_body = f.read()

        try:
            cf.describe_stacks(StackName=stack_name)
            stack_exists = True
        except cf.exceptions.ClientError:
            stack_exists = False

        if stack_exists:
            print(f"🔁 Actualizando stack {stack_name}...")
            try:
                cf.update_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Capabilities=["CAPABILITY_NAMED_IAM"],
                    Parameters=parameters or []
                )
                waiter = cf.get_waiter("stack_update_complete")
            except cf.exceptions.ClientError as e:
                if "No updates are to be performed" in str(e):
                    print(f"ℹ️ No hay cambios en {stack_name}, saltando actualización.")
                    return
                else:
                    raise
        else:
            print(f"🚀 Creando stack {stack_name}...")
            cf.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=["CAPABILITY_NAMED_IAM"],
                Parameters=parameters or []
            )
            waiter = cf.get_waiter("stack_create_complete")

        print("⏳ Esperando a que termine el stack...")
        waiter.wait(StackName=stack_name)
        print(f"✅ Stack {stack_name} desplegado correctamente.\n")

    except cf.exceptions.ClientError as e:
        print(f"❌ Error desplegando stack {stack_name}: {e}")
        sys.exit(1)


def get_ecr_uri(stack_name="champions-ecr"):
    """Obtiene el URI del repositorio ECR compartido."""
    stack = cf.describe_stacks(StackName=stack_name)["Stacks"][0]
    outputs = {o["OutputKey"]: o["OutputValue"] for o in stack["Outputs"]}
    return outputs["RepositoryURI"]


def docker_login(ecr_uri):
    print("🔑 Haciendo login en ECR...")
    login_proc = subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", REGION],
        capture_output=True, text=True, check=True
    )
    subprocess.run(
        ["docker", "login", "--username", "AWS", "--password-stdin", ecr_uri.split('/')[0]],
        input=login_proc.stdout, text=True, check=True
    )


def build_and_push_lambdas(ecr_uri):
    """Construye y sube todas las imágenes Lambda al mismo ECR, usando tags que coinciden con el YAML."""
    docker_login(ecr_uri)
    for lam in LAMBDA_FOLDERS:
        tag = lam["name"].lower()  # coincide con los tags del YAML
        full_tag = f"{ecr_uri}:{tag}"
        print(f"\n📦 Construyendo Lambda {lam['name']} desde {lam['path']}")
        run_command([
            "docker", "buildx", "build", "--platform", "linux/amd64",
            "--provenance=false", "--metadata-file", "metadata.json",
            "--output", "type=docker", "-t", lam['name'].lower(), "."
        ], cwd=lam["path"])
        run_command(["docker", "tag", lam['name'].lower(), full_tag])
        run_command(["docker", "push", full_tag])
        print(f"✅ Lambda {lam['name']} subida a ECR con tag {tag}")


def upload_frontend_to_s3(bucket_name, public_dir="public"):
    print(f"\n🌐 Subiendo frontend al bucket {bucket_name}...")
    for root, _, files in os.walk(public_dir):
        for file in files:
            file_path = os.path.join(root, file)
            key = os.path.relpath(file_path, public_dir)
            content_type = (
                "text/html" if file.endswith(".html")
                else "text/css" if file.endswith(".css")
                else "application/javascript" if file.endswith(".js")
                else "binary/octet-stream"
            )
            s3.upload_file(file_path, bucket_name, key, ExtraArgs={"ContentType": content_type})
            print(f"🆙 Subido: {key}")
    print("✅ Frontend subido correctamente.")


def get_frontend_bucket_name(stack_name="champions-lambda-app"):
    resources = cf.list_stack_resources(StackName=stack_name)["StackResourceSummaries"]
    for res in resources:
        if res["ResourceType"] == "AWS::S3::Bucket" and "FrontendBucket" in res["LogicalResourceId"]:
            return res["PhysicalResourceId"]
    return None


def main():
    print("========== DEPLOY CHAMPIONS SERVERLESS ==========")

    # 1️⃣ DynamoDB compartido
    shared_dynamo_stack = "champions-dynamodb"
    try:
        cf.describe_stacks(StackName=shared_dynamo_stack)
        print(f"✅ Reutilizando base de datos existente: {shared_dynamo_stack}")
    except cf.exceptions.ClientError:
        print(f"🗃️ No se encontró la base de datos. Creando {shared_dynamo_stack}...")
        deploy_stack(shared_dynamo_stack, TEMPLATES["DynamoDB"])

    # 2️⃣ ECR compartido con ECS
    print("🔗 Reutilizando el repositorio ECR existente: champions-ecr")
    ecr_uri = get_ecr_uri()
    print(f"ECR Repository URI: {ecr_uri}")

    # 3️⃣ Lambda Docker builds + push
    build_and_push_lambdas(ecr_uri)

    # 4️⃣ App principal (Lambdas, API Gateway, S3, etc.)
    deploy_stack(
        "champions-lambda-app",
        TEMPLATES["App"],
        parameters=[
            {"ParameterKey": "ECRRepositoryURI", "ParameterValue": ecr_uri},
            {"ParameterKey": "TableName", "ParameterValue": "Champions"}
        ]
    )

    # 5️⃣ Frontend
    bucket_name = get_frontend_bucket_name()
    if bucket_name:
        upload_frontend_to_s3(bucket_name)
        print(f"\n🌍 Frontend disponible en: http://{bucket_name}.s3-website-{REGION}.amazonaws.com")
    else:
        print("⚠️ No se pudo obtener el bucket del frontend, revisa el stack champions-lambda-app.")

    print("\n✅ Todos los recursos serverless desplegados correctamente.")


if __name__ == "__main__":
    main()
