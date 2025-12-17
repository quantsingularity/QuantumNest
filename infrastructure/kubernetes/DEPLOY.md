# Kubernetes Deployment Guide

## Prerequisites

- kubectl configured to access your cluster
- Kubernetes cluster 1.24+
- Sufficient permissions to create resources

## Deployment Steps

### 1. Validate Manifests

```bash
# Validate YAML syntax
yamllint kubernetes/base/*.yaml

# Validate Kubernetes schemas (install kubeval first)
kubeval kubernetes/base/*.yaml

# Dry-run apply
kubectl apply --dry-run=client -f kubernetes/base/
```

### 2. Create Secrets (IMPORTANT: Do this first!)

```bash
# Method 1: Create from literals
kubectl create secret generic quantumnest-backend-secrets \
    --from-literal=database-url="postgresql://user:pass@host:5432/db" \
    --from-literal=jwt-secret="your-secret-here" \
    --namespace=quantumnest-prod

# Method 2: Use external-secrets-operator (recommended for production)
# See security/secrets/external-secrets-operator/

# Method 3: Use sealed-secrets
# kubeseal --format=yaml < app-secrets.yaml > app-secrets-sealed.yaml
```

### 3. Deploy to Kubernetes

```bash
# Apply base manifests
kubectl apply -f kubernetes/base/namespace.yaml
kubectl apply -f kubernetes/base/rbac.yaml
kubectl apply -f kubernetes/base/

# Or use kustomize
kubectl apply -k kubernetes/base/

# Check deployment status
kubectl get all -n quantumnest-prod
kubectl get pods -n quantumnest-prod -w
```

### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods -n quantumnest-prod

# Check logs
kubectl logs -n quantumnest-prod -l app=quantumnest-backend --tail=50

# Check services
kubectl get svc -n quantumnest-prod

# Test connectivity
kubectl port-forward -n quantumnest-prod svc/quantumnest-backend-service 8080:80
curl http://localhost:8080/health
```

## Environment-Specific Deployments

```bash
# Development
kubectl apply -k kubernetes/environments/dev/

# Staging
kubectl apply -k kubernetes/environments/staging/

# Production
kubectl apply -k kubernetes/environments/prod/
```

## Troubleshooting

```bash
# Describe pod for events
kubectl describe pod <pod-name> -n quantumnest-prod

# Check logs
kubectl logs <pod-name> -n quantumnest-prod

# Execute into pod
kubectl exec -it <pod-name> -n quantumnest-prod -- /bin/sh

# Check resource usage
kubectl top pods -n quantumnest-prod
```
