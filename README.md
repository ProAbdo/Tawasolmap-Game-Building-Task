# Game Building Backend

A real-time game simulation backend built with Django, MongoDB, Celery, Redis, and WebSocket support using Django Channels.

## ✨ Features

- **🔐 Player Authentication**: Register and login via WebSocket
- **🏗️ Building Construction**: Start, accelerate, and track building progress
- **💰 Resource Management**: Wood and stone resources with real-time updates
- **⚡ Real-time Notifications**: WebSocket-based live updates
- **🔄 Background Tasks**: Celery for scheduled building completion
- **📊 MongoDB Database**: NoSQL database with embedded documents
- **🚀 Scalable Architecture**: Microservices with Docker

## 🛠️ Tech Stack

- **Backend**: Django 5.2 ASGI
- **Database**: MongoDB with django-mongodb-backend
- **Message Broker**: Redis
- **Task Queue**: Celery
- **WebSocket**: Django Channels
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- [Docker](https://www.docker.com/) (v20.10)
- [Docker Compose](https://docs.docker.com/compose/) (v2)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ProAbdo/Tawasolmap-Game-Building-Task.git
cd game_building
```

### 2. Start All Services

```bash
docker-compose up --build
```

This will start:

- **Backend**: Django ASGI server on port 8000
- **Celery Worker**: Background task processor
- **MongoDB**: Database on port 27017
- **Redis** : Message broker on port 6379

### 3. Access the Application

- **Backend API**: http://localhost:8000
- **MongoDB**: [mongodb://localhost:27017](mongodb://localhost:27017)
- **Redis**: [redis://localhost:6379/](redis://localhost:6379/)

## 🔧 Environment Variables

The following environment variables are configured in `docker-compose.yaml`:

| Variable                 | Description               | Default                               |
| ------------------------ | ------------------------- | ------------------------------------- |
| `DJANGO_SETTINGS_MODULE` | Django settings module    | `game_building.config.settings`       |
| `DJANGO_DEBUG`           | Debug mode                | `False`                               |
| `ALLOWED_HOSTS`          | Allowed hosts             | `*`                                   |
| `MONGO_URI`              | MongoDB connection string | `mongodb://mongo:27017/game_building` |
| `REDIS_URL`              | Redis connection string   | `redis://redis:6379/0`                |
| `CELERY_BROKER_URL`      | Celery broker URL         | `redis://redis:6379/0`                |
| `CELERY_RESULT_BACKEND`  | Celery result backend     | `redis://redis:6379/0`                |
| `CHANNEL_LAYERS_HOSTS`   | Channels Redis hosts      | `redis:6379`                          |

## 🌐 WebSocket API

### Connection

- **URL**: `ws://localhost:8000/ws/game/`
- **Protocol**: WebSocket

### Message Types

| Type                  | Description                 | Authentication Required |
| --------------------- | --------------------------- | ----------------------- |
| `register`            | Register new player         | ❌                      |
| `login`               | Login as player             | ❌                      |
| `get_player_info`     | Get player information      | ✅                      |
| `update_resources`    | Update player resources     | ✅                      |
| `start_building`      | Start building construction | ✅                      |
| `accelerate_building` | Speed up construction       | ✅                      |
| `create_building`     | Create new building type    | ❌                      |

## 🧪 Testing WebSocket API

### Using Postman

1. **Create WebSocket Request**:

   - Open Postman
   - Click NewWebSocket Request"
   - Enter URL: `ws://localhost:8000/ws/game/`
   - Click "Connect"

2. **Send Messages**:

   ```json
   {
     "type": "register",
     "username": "testplayer",
     "password": "secret123",
     "email": "test@example.com"
   }
   ```

### Using Chrome Console

1. **Open Developer Tools**:

   - Press `F12` or right-click →Inspect"
   - Go toConsole" tab

2. **Connect to WebSocket**:

   ```javascript
   const ws = new WebSocket("ws://localhost:8000/ws/game/");

   ws.onopen = function () {
     console.log("Connected to WebSocket");
   };

   ws.onmessage = function (event) {
     console.log("Received:", JSON.parse(event.data));
   };

   ws.onerror = function (error) {
     console.error("WebSocket error:", error);
   };
   ```

3. **Send Messages**:

   ```javascript
   // Register
   ws.send(
     JSON.stringify({
       type: register,
       username: "testplayer",
       password: "secret123",
       email: "test@example.com",
     })
   );
   // Login
   ws.send(
     JSON.stringify({
       type: "login",
       username: "testplayer",
       password: "secret123",
     })
   );
   // Get player info
   ws.send(
     JSON.stringify({
       type: get_player_info,
     })
   );
   ```

## 📝 API Examples

### 1. Player Registration

```json
{
  "type": "register",
  "username": "player1",
  "password": "secret123",
  "email": "player1@example.com"
}
```

**Response**:

```json
{
  "type": "register_success",
  "player": {
    "id": "player_id",
    "username": "player1",
    "email": "player1@example.com",
    "resources": {
      "wood": 10,
      "stone": 50,
      "buildings": []
    }
  }
}
```

### 2. Player Login

```json
{
  "type": "login",
  "username": "player1",
  "password": "secret123"
}
```

**Response**:

```json
{
  "type": "login_success",
  "player": {
    "id": "player_id",
    "username": "player1",
    "email": "player1@example.com",
    "resources": {
      "wood": 10,
      "stone": 50,
      "buildings": []
    }
  }
}
```

### 3. Get Player Information

```json
{
  "type": "get_player_info"
}
```

**Response**:

```json
{
  "type": "player_info",
  "player": {
    "id": "player_id",
    "username": "player1",
    "email": "player1@example.com",
    "resources": {
      "wood": 10,
      "stone": 50,
      "buildings": [
        {
          "building_id": "1",
          "status": "progress",
          "started_at": "2025-07-07T07:00:00Z",
          "finish_eta": "2025-07-07T07:00:00Z",
          "celery_task_id": "task_id"
        }
      ]
    }
  }
}
```

### 4. Update Resources

```json
{
  "type": "update_resources",
  "wood": 200,
  "stone": 150
}
```

**Response**:

```json
{
  "type": "update_success",
  "player": {
    "id": "player_id",
    "username": "player1",
    "resources": {
      "wood": 200,
      "stone": 150,
      "buildings": []
    }
  }
}
```

### 5Start Building

```json
{
  "type": "start_building",
  "building_id": 1
}
```

**Response**:

```json
{
  "type": "building_started",
  "building_id": 1,
  "completion_time": "2025-07-17T00:10:00.00"
}
```

### 6. Accelerate Building

```json
{
  "type": "accelerate_building",
  "building_id": 1,
  "percent": 50
}
```

**Response**:

```json
{
  "type": "building_accelerated",
  "building_id": 1,
  "new_finish_eta": "2025-07-17T00:05:00"
}
```

## 🔄 Real-time Notifications

The server sends automatic notifications for:

### Building Completed

```json
{
  "type": "building_completed",
  "building_id": 1
}
```

### Player Updated

```json
{
  "type": "player_updated",
  "player": {
    "id": "player_id",
    "username": "player1",
    "resources": {
      "wood": 10,
      "stone": 50,
      "buildings": []
    }
  }
}
```

## 📁 Project Structure

```
game_building/
├── apps/
│   ├── players/          # Player management
│   │   ├── models.py     # Player and PlayerBuilding models
│   │   ├── services.py   # Business logic
│   │   ├── serializers.py # DRF serializers
│   │   └── tasks.py      # Celery tasks
│   └── buildings/        # Building management
│       ├── models.py     # Building model
│       ├── services.py   # Building logic
│       └── serializers.py # Building serializers
├── config/               # Django settings
│   ├── settings.py       # Main settings
│   ├── urls.py          # URL configuration
│   ├── asgi.py          # ASGI application
│   └── celery.py        # Celery configuration
├── consumers.py         # WebSocket consumers
├── routing.py           # WebSocket routing
├── docker-compose.yaml  # Docker services
└── Dockerfile          # Backend container
```

**Happy Building! ✨**
