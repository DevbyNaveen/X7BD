# 🚀 Deployment Guide - Analytics Dashboard Service

## 📋 Pre-Deployment Checklist

- [ ] Environment variables configured
- [ ] Database schema deployed
- [ ] Dependencies installed
- [ ] Health checks verified
- [ ] API documentation reviewed
- [ ] WebSocket connections tested

---

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# Service Configuration
ANALYTICS_PORT=8060
ANALYTICS_HOST=0.0.0.0
NODE_ENV=production
LOG_LEVEL=info

# Database (Supabase)
SUPABASE_URL=https://ydlmkvkfmmnitfhjqakt.supabase.co
SUPABASE_SERVICE_KEY=your_service_key_here
SUPABASE_PROJECT_ID=ydlmkvkfmmnitfhjqakt

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=1000

# Analytics
ANALYTICS_CACHE_TTL=300
METRICS_AGGREGATION_INTERVAL=60

# Optional: External Services
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your_key_here
AWS_S3_BUCKET=your_bucket_name
```

---

## 🐳 Docker Deployment

### 1. Create Dockerfile

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8060

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8060/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8060", "--workers", "4"]
```

### 2. Build Docker Image

```bash
docker build -t analytics-dashboard-service:latest .
```

### 3. Run Container

```bash
docker run -d \
  --name analytics-dashboard \
  -p 8060:8060 \
  --env-file .env \
  --restart unless-stopped \
  analytics-dashboard-service:latest
```

### 4. Docker Compose

```yaml
version: '3.8'

services:
  analytics-dashboard:
    build: .
    container_name: analytics-dashboard-service
    ports:
      - "8060:8060"
    environment:
      - ANALYTICS_PORT=8060
      - NODE_ENV=production
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8060/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

Run with:
```bash
docker-compose up -d
```

---

## ☸️ Kubernetes Deployment

### 1. Deployment Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-dashboard
  namespace: x7ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: analytics-dashboard
  template:
    metadata:
      labels:
        app: analytics-dashboard
    spec:
      containers:
      - name: analytics-dashboard
        image: analytics-dashboard-service:latest
        ports:
        - containerPort: 8060
        env:
        - name: ANALYTICS_PORT
          value: "8060"
        - name: SUPABASE_URL
          valueFrom:
            secretKeyRef:
              name: supabase-credentials
              key: url
        - name: SUPABASE_SERVICE_KEY
          valueFrom:
            secretKeyRef:
              name: supabase-credentials
              key: service-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8060
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8060
          initialDelaySeconds: 20
          periodSeconds: 5
```

### 2. Service Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: analytics-dashboard-service
  namespace: x7ai
spec:
  selector:
    app: analytics-dashboard
  ports:
  - protocol: TCP
    port: 8060
    targetPort: 8060
  type: LoadBalancer
```

### 3. Secrets Configuration

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: supabase-credentials
  namespace: x7ai
type: Opaque
stringData:
  url: "https://ydlmkvkfmmnitfhjqakt.supabase.co"
  service-key: "your_service_key_here"
```

### 4. Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace x7ai

# Apply secrets
kubectl apply -f k8s/secrets.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Verify deployment
kubectl get pods -n x7ai
kubectl get svc -n x7ai
```

---

## 🌐 Cloud Platform Deployments

### AWS (Elastic Beanstalk)

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init -p python-3.9 analytics-dashboard

# Create environment
eb create analytics-dashboard-prod

# Deploy
eb deploy

# Open application
eb open
```

### Google Cloud (Cloud Run)

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/analytics-dashboard

# Deploy to Cloud Run
gcloud run deploy analytics-dashboard \
  --image gcr.io/PROJECT_ID/analytics-dashboard \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8060 \
  --set-env-vars SUPABASE_URL=$SUPABASE_URL,SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY
```

### Azure (Container Instances)

```bash
# Login to Azure
az login

# Create resource group
az group create --name analytics-rg --location eastus

# Deploy container
az container create \
  --resource-group analytics-rg \
  --name analytics-dashboard \
  --image analytics-dashboard-service:latest \
  --dns-name-label analytics-dashboard \
  --ports 8060 \
  --environment-variables \
    ANALYTICS_PORT=8060 \
    SUPABASE_URL=$SUPABASE_URL \
    SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
name: Deploy Analytics Dashboard

on:
  push:
    branches: [ main ]
    paths:
      - 'services/analytics-dashboard-service/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        cd services/analytics-dashboard-service
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd services/analytics-dashboard-service
        pytest tests/
    
    - name: Build Docker image
      run: |
        cd services/analytics-dashboard-service
        docker build -t analytics-dashboard:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push analytics-dashboard:${{ github.sha }}
    
    - name: Deploy to production
      run: |
        # Your deployment script here
        kubectl set image deployment/analytics-dashboard \
          analytics-dashboard=analytics-dashboard:${{ github.sha }}
```

---

## 📊 Monitoring Setup

### Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'analytics-dashboard'
    static_configs:
      - targets: ['analytics-dashboard:8060']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard

Import the following dashboard JSON for monitoring:

```json
{
  "dashboard": {
    "title": "Analytics Dashboard Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(analytics_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

---

## 🔐 Security Hardening

### 1. SSL/TLS Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name analytics.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8060;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/v1/ws/ {
        proxy_pass http://localhost:8060;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. Environment Security

```bash
# Use secrets management
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name analytics-dashboard/supabase \
  --secret-string '{"url":"...","key":"..."}'

# Kubernetes Secrets
kubectl create secret generic supabase-credentials \
  --from-literal=url=$SUPABASE_URL \
  --from-literal=service-key=$SUPABASE_SERVICE_KEY
```

### 3. Rate Limiting

```python
# Add to main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/analytics/realtime/{business_id}")
@limiter.limit("60/minute")
async def get_realtime_analytics(request: Request, business_id: UUID):
    # ... endpoint code
```

---

## 🧪 Production Testing

### Health Check Verification

```bash
# Liveness
curl http://your-domain:8060/health/live

# Readiness
curl http://your-domain:8060/health/ready

# Full health
curl http://your-domain:8060/health
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://your-domain:8060/api/v1/analytics/realtime/BUSINESS_ID

# Using wrk
wrk -t12 -c400 -d30s http://your-domain:8060/api/v1/menu/items?business_id=BUSINESS_ID
```

### WebSocket Testing

```javascript
// Test WebSocket connection
const ws = new WebSocket('wss://your-domain/api/v1/ws/dashboard/BUSINESS_ID');

ws.onopen = () => console.log('Connected');
ws.onerror = (error) => console.error('Error:', error);
ws.onmessage = (event) => console.log('Message:', event.data);
```

---

## 📈 Scaling Guidelines

### Horizontal Scaling

```bash
# Kubernetes
kubectl scale deployment analytics-dashboard --replicas=5

# Docker Swarm
docker service scale analytics-dashboard=5
```

### Auto-scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: analytics-dashboard-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: analytics-dashboard
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 🔄 Backup & Recovery

### Database Backups

```bash
# Automated Supabase backups are handled by the platform
# For additional backups:

# Export data
curl -X GET "http://your-domain:8060/api/v1/export/BUSINESS_ID?data_type=all&format=json" \
  -H "Authorization: Bearer $TOKEN" \
  -o backup-$(date +%Y%m%d).json
```

### Disaster Recovery

```bash
# 1. Restore from backup
# 2. Redeploy service
kubectl apply -f k8s/

# 3. Verify health
kubectl get pods -n x7ai
curl http://your-domain:8060/health
```

---

## 📝 Post-Deployment Checklist

- [ ] Service is running and healthy
- [ ] All endpoints responding correctly
- [ ] WebSocket connections working
- [ ] Database connectivity verified
- [ ] Monitoring dashboards configured
- [ ] Alerts set up
- [ ] SSL/TLS configured
- [ ] Rate limiting active
- [ ] Backups scheduled
- [ ] Documentation updated
- [ ] Team notified

---

## 🆘 Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
docker logs analytics-dashboard
kubectl logs -f deployment/analytics-dashboard

# Verify environment
env | grep SUPABASE
```

**Database connection errors:**
```bash
# Test connection
curl -X GET "http://localhost:8060/health"

# Check Supabase status
curl https://status.supabase.com/api/v2/status.json
```

**WebSocket issues:**
```bash
# Check WebSocket endpoint
wscat -c ws://localhost:8060/api/v1/ws/dashboard/BUSINESS_ID

# Verify proxy configuration
nginx -t
```

---

## 📞 Support

For deployment issues:
1. Check service logs
2. Verify environment variables
3. Test database connectivity
4. Review monitoring dashboards
5. Contact DevOps team

---

**🎉 Your analytics dashboard service is now production-ready!**
