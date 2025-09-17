# MyCandidate Deployment Guide

## Quick Start

### Local Development with Docker

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd mycandidate
   ```

2. **Start Services**
   ```bash
   docker-compose up --build
   ```

3. **Access Application**
   - Web Interface: http://localhost:8080
   - API Endpoint: http://localhost:8080/api/v1/wards/WARD001/candidates

### Testing the API

```bash
# Test the new ward candidates endpoint
curl http://localhost:8080/api/v1/wards/WARD001/candidates

# List available wards
curl http://localhost:8080/api/v1/wards

# Test with specific candidate type
curl http://localhost:8080/api/v1/wards/WARD001/candidates?candidate_type=municipal
```

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test file
pytest tests/test_api_routes.py -v

# Run with coverage
pytest tests/ --cov=main --cov-report=html
```

## AWS Deployment

### Prerequisites
- AWS CLI configured
- Docker installed
- Terraform (optional, for infrastructure)

### Step 1: Create ECR Repository
```bash
aws ecr create-repository --repository-name mycandidate --region us-east-1
```

### Step 2: Build and Push Image
```bash
# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag image
docker build -t mycandidate .
docker tag mycandidate:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/mycandidate:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/mycandidate:latest
```

### Step 3: Create ECS Cluster
```bash
aws ecs create-cluster --cluster-name mycandidate-cluster
```

### Step 4: Create Task Definition
```json
{
  "family": "mycandidate-task-definition",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "mycandidate",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/mycandidate:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "SQLALCHEMY_DATABASE_URI",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:mycandidate/db-uri"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mycandidate",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Step 5: Create ECS Service
```bash
aws ecs create-service \
  --cluster mycandidate-cluster \
  --service-name mycandidate-service \
  --task-definition mycandidate-task-definition \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

## Environment Configuration

### Required Environment Variables
```bash
# Database
SQLALCHEMY_DATABASE_URI=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://host:port/0

# Application
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
SITE_URL=https://your-domain.com

# AWS (for deployment)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### Secrets Management
Store sensitive data in AWS Secrets Manager:
```bash
# Database URI
aws secretsmanager create-secret \
  --name "mycandidate/db-uri" \
  --secret-string "postgresql://user:password@host:port/database"

# Redis URL
aws secretsmanager create-secret \
  --name "mycandidate/redis-url" \
  --secret-string "redis://host:port/0"
```

## Monitoring Setup

### CloudWatch Logs
```bash
# Create log group
aws logs create-log-group --log-group-name /ecs/mycandidate
```

### CloudWatch Alarms
```bash
# High CPU usage alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "MyCandidate-High-CPU" \
  --alarm-description "High CPU usage detected" \
  --metric-name "CPUUtilization" \
  --namespace "AWS/ECS" \
  --statistic "Average" \
  --period 300 \
  --threshold 80 \
  --comparison-operator "GreaterThanThreshold" \
  --dimensions Name=ServiceName,Value=mycandidate-service Name=ClusterName,Value=mycandidate-cluster
```

## Troubleshooting

### Common Issues

1. **Container won't start**
   - Check environment variables
   - Verify database connectivity
   - Check logs: `docker logs <container-id>`

2. **API endpoint not working**
   - Verify database has candidate data
   - Check ward_id format
   - Review application logs

3. **ECS deployment fails**
   - Check task definition
   - Verify IAM permissions
   - Check ECR image exists

### Debug Commands
```bash
# Check container logs
docker-compose logs web

# Check database connection
docker-compose exec db psql -U mycandidate -d mycandidate_db -c "SELECT COUNT(*) FROM candidates;"

# Test API locally
curl -v http://localhost:5000/api/v1/wards

# Check ECS service status
aws ecs describe-services --cluster mycandidate-cluster --services mycandidate-service
```

## Security Checklist

- [ ] Environment variables secured
- [ ] Database credentials in Secrets Manager
- [ ] Security groups properly configured
- [ ] SSL/TLS certificates installed
- [ ] Regular security scans enabled
- [ ] Backup strategy implemented
- [ ] Monitoring and alerting configured

## Support

For deployment issues or questions:
1. Check the troubleshooting section
2. Review application logs
3. Consult the architecture documentation
4. Contact the development team
