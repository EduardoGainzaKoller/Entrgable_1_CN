#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script: deploy_champions.py
Descripción: Despliega la infraestructura de Champions en AWS
Componentes:
  1. ECR Repository
  2. DynamoDB Table
  3. ECS Fargate + API Gateway + NLB
Requisitos previos:
  - AWS CLI configurado o credenciales en ~/.aws/credentials
  - Docker instalado
  - Permisos de CloudFormation, ECS, ECR, IAM, DynamoDB
"""

import boto3
import shutil
import subprocess
import sys
import time
from urllib.parse import urlparse

# =========================
# Configuración inicial
# =========================
REGION = "us-east-1"

TEMPLATES = {
    "ECR": "ecr.yaml",
    "DynamoDB": "dynamodb.yaml",
    "ECS": "main.yaml"
}

# =========================
# Validar prerequisitos
# =========================
if not shutil.which("aws"):
    print("AWS CLI no está instalado. Instálalo antes de continuar.")
    sys.exit(1)

if not shutil.which("docker"):
    print("Docker no está instalado o no está en el PATH.")
    sys.exit(1)

print("========== DEPLOY CHAMPIONS INFRASTRUCTURE ==========")

# =========================
# Inicializar clientes boto3
# =========================
ec2 = boto3.client("ec2", region_name=REGION)
cf = boto3.client("cloudformation", region_name=REGION)

# =========================
# Obtener VPC y Subnets por defecto
# =========================
print("Obteniendo VPC y Subnets por defecto...")

vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])
if not vpcs["Vpcs"]:
    print("No se encontró una VPC por defecto.")
    sys.exit(1)

vpc_id = vpcs["Vpcs"][0]["VpcId"]

subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])
subnet_ids = [subnet["SubnetId"] for subnet in subnets["Subnets"]]

print(f"VPC ID: {vpc_id}")
print(f"Subnets: {', '.join(subnet_ids)}")

# =========================
# Función para desplegar CloudFormation
# =========================
def deploy_stack(stack_name, template_file, parameters=None):
    """
    Despliega un stack de CloudFormation.
    """
    try:
        # Leer template
        with open(template_file, "r") as f:
            template_body = f.read()

        # Verificar si el stack existe
        try:
            cf.describe_stacks(StackName=stack_name)
            stack_exists = True
        except cf.exceptions.ClientError:
            stack_exists = False

        if stack_exists:
            print(f"Actualizando stack {stack_name}...")
            cf.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=["CAPABILITY_NAMED_IAM"],
                Parameters=parameters or []
            )
            waiter = cf.get_waiter('stack_update_complete')
        else:
            print(f"Creando stack {stack_name}...")
            cf.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=["CAPABILITY_NAMED_IAM"],
                Parameters=parameters or []
            )
            waiter = cf.get_waiter('stack_create_complete')

        print("Esperando a que el stack termine de desplegarse...")
        waiter.wait(StackName=stack_name)
        print(f"{stack_name} desplegado correctamente.")

    except cf.exceptions.ClientError as e:
        if "No updates are to be performed" in str(e):
            print(f"{stack_name} ya está actualizado, sin cambios.")
        else:
            print(f"Error al desplegar stack {stack_name}: {e}")
            sys.exit(1)

# =========================
# 1. Desplegar ECR Repository
# =========================
deploy_stack("champions-ecr", TEMPLATES["ECR"])

# =========================
# 2. Subir imagen Docker a ECR
# =========================
# Obtener URI del repositorio desde outputs
response = cf.describe_stacks(StackName="champions-ecr")
repository_uri = next(
    o['OutputValue'] for o in response['Stacks'][0]['Outputs'] if o['OutputKey'] == 'RepositoryURI'
)

print(f"Repositorio ECR: {repository_uri}")

# Login a ECR
print("Haciendo login en ECR...")
login_cmd = f"aws ecr get-login-password --region {REGION}"
login_proc = subprocess.run(login_cmd.split(), capture_output=True, text=True)
if login_proc.returncode != 0:
    print(f"Error en login ECR: {login_proc.stderr}")
    sys.exit(1)

docker_login_cmd = f"docker login --username AWS --password-stdin {repository_uri}"
docker_login_proc = subprocess.run(docker_login_cmd.split(), input=login_proc.stdout, text=True)
if docker_login_proc.returncode != 0:
    print(f"Error en docker login: {docker_login_proc.stderr}")
    sys.exit(1)

# Construir, taggear y subir imagen
print("Construyendo imagen Docker...")
subprocess.run(["docker", "build", "-t", "champions-api:latest", "."], check=True)
subprocess.run(["docker", "tag", "champions-api:latest", f"{repository_uri}:latest"], check=True)
subprocess.run(["docker", "push", f"{repository_uri}:latest"], check=True)

print(f"Imagen Docker subida correctamente a ECR: {repository_uri}")

# =========================
# 3. Desplegar DynamoDB
# =========================
deploy_stack("champions-dynamodb", TEMPLATES["DynamoDB"])

# =========================
# 4. Desplegar ECS + API Gateway + NLB
# =========================
image_name = repository_uri.split("/")[-1] + ":latest"

deploy_stack(
    "champions-ecs-api",
    TEMPLATES["ECS"],
    parameters=[
        {"ParameterKey": "VpcId", "ParameterValue": vpc_id},
        {"ParameterKey": "SubnetIds", "ParameterValue": ",".join(subnet_ids)},
        {"ParameterKey": "ImageName", "ParameterValue": image_name}
    ]
)

# =========================
# Obtener URL final de la API
# =========================
response = cf.describe_stacks(StackName="champions-ecs-api")
api_url = next(
    (o['OutputValue'] for o in response['Stacks'][0]['Outputs'] if o['OutputKey'] == 'ApiUrl'),
    None
)

print("======================================================")
print("Despliegue completado exitosamente.")
if api_url:
    print(f"URL de la API: {api_url}")
print("======================================================")
