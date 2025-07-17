# 🏗️ Game Building Backend

A Django backend for real-time building simulation game using Django, MongoDB, WebSocket, Redis , and Celery.

## 📋 Project Overview

This project is a comprehensive backend system for a building construction game where players can:

- Register and login
- Build various structures
- Manage resources (wood and stone)
- Accelerate building construction
- Receive real-time notifications when buildings complete

## 🏗️ Technical Architecture

### Technologies Used

- **Django 5.2** - Main web framework
- **MongoDB** - Database (with django_mongodb_backend)
- **Django Channels** - WebSocket support for real-time communication
- **Celery** - Background task processing
- **Redis** - Message broker and caching
- **Docker & Docker Compose** - Application containerization

### Project Structure

```
game_building/
├── apps/
│   ├── players/          # Players application
│   │   ├── models.py     # Player and resources models
│   │   ├── services.py   # Business logic
│   │   ├── serializers.py # Data serialization
│   │   └── tasks.py      # Celery tasks
│   └── buildings/        # Buildings application
│       ├── models.py     # Building models
│       ├── services.py   # Building logic
│       └── serializers.py
├── config/               # Django settings
├── consumers.py          # WebSocket handlers
├── routing.py           # WebSocket routing
└── docker-compose.yaml  # Docker configuration
```

## 🚀 Prerequisites

### Required

- [Docker](https://www.docker.com/get-started) (version20.10
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0+)

### Optional

-Git](https://git-scm.com/) - for cloning the repository

- [Postman](https://www.postman.com/) or any WebSocket client for testing

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd game_building
```

### 2. Run the Project

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Verify Services

After startup, the following services will be available:

- **Backend API**: http://localhost:80**MongoDB**: localhost:27017- **Redis**: localhost:6379. Stop the Project

```bash
docker-compose down
```

## 🔧 Environment Variables

Environment variables are set in `docker-compose.yaml`:

| Variable                 | Default Value                           | Description               |
| ------------------------ | --------------------------------------- | ------------------------- |
| `DJANGO_SETTINGS_MODULE` | `game_building.config.settings`         | Django settings module    |
| `DJANGO_DEBUG`           | `False`                                 | Development mode          |
| `SECRET_KEY`             | `django-insecure-...`                   | Security key              |
| `MONGO_URI`              | `mongodb://mongo:2717uilding`           | MongoDB connection string |
| `REDIS_URL`              | `redis://redis:6379/0`                  | Redis connection string   |
| `CELERY_BROKER_URL`      | `redis://redis:6379/0 Celery broker URL |
| `CHANNEL_LAYERS_HOSTS`   | `redis:6379`                            | WebSocket channel hosts   |

## 📡 WebSocket API

### Endpoint

```
ws://localhost:80/ws/game/
```

### Supported Message Types

#### 1. Register New Player

```json
{
 type: ster,
  username": "player1,
  password": "secret123  email: "player1@example.com"
}
```

**Response:**

```json
{
 type":register_success",
 player": {
  id": player_id,username": "player1  email: "player1@example.com",
 resources: {
      wood":100
   stone: 50
    },
   buildings": ]
  }
}
```

####2. Login

```json
[object Object] type": "login,
  username": "player1,
  password": "secret123"
}
```

**Response:**

```json
[object Object]type": login_success",
  player: { ... }
}
```

####3lding Construction

```json
[object Object]type:start_building",
 building_id": 1
}
```

**Response:**

````json
{
 type:building_started",
 building_id": 1  completion_time: 20250717T00:10.000`

#### 4. Accelerate Building
```json
{
type": "accelerate_building",
  building_id: 1,
percent": 50
}
````

**Response:**

````json
{
 type":building_accelerated",
  building_id":1
 new_finish_eta: 20250717T00:05.000``

#### 5. Update Resources
```json
{type":update_resources,
wood: 200stone": 150
}
````

**Response:**

```json
{
 type:update_success",
  player: { ... }
}
```

#### 6. Get Player Information

```json
{
  "type": get_player_info"
}
```

**Response:**

```json
{type: player_info",
  player:{ ... }
}
```

### Real-time Notifications

#### Building Completed

```json
{
 type": "building_completed",
 building_id": 1
}
```

#### Player Data Updated

```json
{
type:player_updated",
  player:[object Object]... }
}
```

## 🧪 Complete Testing Scenario

### Step1nnect to WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/game/);
```

### Step 2: Register New Player

```javascript
ws.send(JSON.stringify({
 type: ster,username:testPlayer,password": "test123,email":test@example.com"
}));
```

### Step3lding Construction

```javascript
ws.send(JSON.stringify([object Object]type:start_building",
  building_id: 1}));
```

### Step 4: Monitor Notifications

```javascript
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Received:', data);

  if (data.type === 'building_completed')[object Object]
    console.log('Building completed!);
  }
};
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Redis Connection Error

```
ConnectionError: Error connecting to localhost:6379
```

**Solution:** Ensure `CHANNEL_LAYERS_HOSTS` is set to `redis:6379` in Docker environment.

#### 2. Module Import Error

```
ModuleNotFoundError: No module named 'config'
```

**Solution:** Verify all app/module names are prefixed with `game_building.` in settings and apps.py.

#### 3. MongoDB Connection Error

```
ConnectionError: MongoDB connection failed
```

**Solution:** Ensure MongoDB service is running and `MONGO_URI` is correct.

#### 4. Celery Task Error

```
Celery worker not processing tasks
```

**Solution:** Check Celery logs:

```bash
docker-compose logs celery
```

### Useful Diagnostic Commands

```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs celery
docker-compose logs mongo

# Restart specific service
docker-compose restart backend

# Remove all data and rebuild
docker-compose down -v
docker-compose up --build
```

## 📊 Data Management

### Backup

```bash
# Backup database
docker-compose exec mongo mongodump --db game_building --out /backup

# Restore backup
docker-compose exec mongo mongorestore --db game_building /backup/game_building
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats

# Monitor application logs
docker-compose logs -f backend
```

## 🤝 Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -mAdd some AmazingFeature`)
   4.Push to the branch (`git push origin feature/AmazingFeature`)
4. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

If you encounter any issues or have questions:

- Open an issue on GitHub
- Check the troubleshooting section above
- Review Docker logs

---

**This project is developed using Django, MongoDB, and WebSocket to provide an interactive real-time gaming experience.**
