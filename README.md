# Product CSV Importer

A scalable Django web application for importing and managing products from CSV files. Built to handle large datasets (up to 500,000 records) with real-time progress tracking, webhook notifications, and a clean, intuitive user interface.

## Features

### 📤 CSV File Upload
- Upload large CSV files (up to 500,000 products) via drag-and-drop or file selection
- Real-time progress tracking with visual progress bar and statistics
- Automatic duplicate handling based on case-insensitive SKU
- Chunked processing for optimal memory usage
- Error handling with detailed failure reporting

### 📦 Product Management
- View, create, update, and delete products through a web interface
- Advanced filtering by SKU, name, description, and active status
- Paginated product listings with navigation controls
- Bulk delete functionality with confirmation dialogs
- Active/inactive product status management

### 🔔 Webhook Configuration
- Configure multiple webhooks for different event types
- Support for product lifecycle events (created, updated, deleted)
- Import job events (completed, failed)
- Test webhook delivery with visual confirmation
- Enable/disable webhooks individually
- SSL signature support for webhook security

### ⚡ Asynchronous Processing
- Celery-based background task processing
- Non-blocking CSV imports
- Real-time progress updates via HTTP polling
- Scalable architecture for handling large datasets

## Tech Stack

- **Web Framework**: Django 4.2
- **Task Queue**: Celery 5.5 with Redis
- **Database**: PostgreSQL
- **API**: Django REST Framework
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **Deployment**: Render (or any platform supporting Python)

## Project Structure

```
product_importer/
├── base/                    # Base app with reusable components
│   ├── models.py           # Abstract base models (UUID, timestamps, soft delete)
│   ├── dbio.py             # Base database I/O operations
│   ├── views.py            # Abstract API views
│   └── choices.py          # Global choice constants
├── products/               # Products app
│   ├── models.py           # Product, Webhook, ImportJob models
│   ├── handlers/           # Business logic handlers
│   │   ├── csv_processor.py
│   │   ├── csv_upload_handler.py
│   │   ├── product_handler.py
│   │   └── webhook_handler.py
│   ├── tasks.py            # Celery tasks
│   ├── views.py            # API endpoints and page views
│   └── templates/          # HTML templates
├── product_importer/       # Django project settings
│   ├── settings.py
│   ├── celery.py           # Celery configuration
│   └── urls.py
├── start.sh                # Production startup script (Gunicorn + Celery)
└── requirements.txt        # Python dependencies
```

## Prerequisites

- Python 3.9+
- PostgreSQL
- Redis (for Celery broker and result backend)
- pip

## Local Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd product_importer
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create a `.env` file or export the following variables:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/product_importer"
export REDIS_URL="redis://localhost:6379/0"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
export SECRET_KEY="your-secret-key-here"
export DEBUG="True"
export DJANGO_SETTINGS_MODULE="product_importer.settings"
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Collect Static Files

```bash
python manage.py collectstatic
```

### 7. Start Redis

```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Or use Docker
docker run -d -p 6379:6379 redis:latest
```

### 8. Start Celery Worker

In a separate terminal:

```bash
celery -A product_importer worker --loglevel=info
```

### 9. Start Django Development Server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## CSV File Format

The CSV file should have the following columns:

- `sku` (required): Product SKU (case-insensitive, unique)
- `name` (required): Product name
- `description` (optional): Product description

Example CSV:

```csv
sku,name,description
PROD001,Product One,This is product one
PROD002,Product Two,This is product two
prod003,Product Three,This is product three
```

**Note**: SKUs are case-insensitive. If a product with the same SKU (case-insensitive) already exists, it will be updated with the new data.

## API Endpoints

### CSV Upload
- `POST /api/upload/` - Upload CSV file
- `GET /api/import/<job_id>/status/` - Get import job status

### Products
- `GET /api/products/` - List products (with filtering and pagination)
- `POST /api/products/` - Create product
- `GET /api/products/<product_id>/` - Get product details
- `PUT /api/products/<product_id>/` - Update product
- `DELETE /api/products/<product_id>/` - Delete product
- `DELETE /api/products/bulk-delete/` - Delete all products

### Webhooks
- `GET /api/webhooks/` - List webhooks
- `POST /api/webhooks/` - Create webhook
- `GET /api/webhooks/<webhook_id>/` - Get webhook details
- `PUT /api/webhooks/<webhook_id>/` - Update webhook
- `DELETE /api/webhooks/<webhook_id>/` - Delete webhook
- `POST /api/webhooks/<webhook_id>/test/` - Test webhook delivery

### Health Check
- `GET /health/` - Health check endpoint

## Webhook Events

The following events trigger webhooks:

- `product.created` - When a product is created
- `product.updated` - When a product is updated
- `product.deleted` - When a product is deleted
- `import.completed` - When CSV import completes successfully
- `import.failed` - When CSV import fails

### Webhook Payload Format

```json
{
  "event_type": "product.created",
  "timestamp": 1701234567,
  "data": {
    "product": {
      "uuid": "...",
      "sku": "PROD001",
      "name": "Product One",
      "description": "...",
      "active": true,
      "created_at": "2025-11-29T10:00:00Z"
    }
  }
}
```

### Webhook Headers

- `X-Webhook-Event`: Event type
- `X-Webhook-Timestamp`: Unix timestamp
- `X-Webhook-Signature`: HMAC-SHA256 signature (if secret is configured)

## Deployment

### Render Deployment

1. **Create a new Web Service** on Render
2. **Connect your GitHub repository**
3. **Set Environment Variables**:
   - `DATABASE_URL` - PostgreSQL connection string
   - `REDIS_URL` - Redis connection string (use `rediss://` for TLS)
   - `CELERY_BROKER_URL` - Same as REDIS_URL
   - `CELERY_RESULT_BACKEND` - Same as REDIS_URL
   - `SECRET_KEY` - Django secret key
   - `DEBUG` - Set to `False` for production
   - `ALLOWED_HOSTS` - Your Render service URL

4. **Build Command**:
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```

5. **Start Command**:
   ```bash
   bash start.sh
   ```

The `start.sh` script runs both Celery worker and Gunicorn in a single service.

### Environment Variables for Production

```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=rediss://default:password@host:6379
CELERY_BROKER_URL=rediss://default:password@host:6379
CELERY_RESULT_BACKEND=rediss://default:password@host:6379
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
DJANGO_SETTINGS_MODULE=product_importer.settings
```

## Performance Considerations

- **Chunked Processing**: CSV files are processed in chunks of 5,000 records
- **Bulk Operations**: Uses Django's `bulk_create` and `bulk_update` for efficiency
- **Database Indexing**: SKU and common query fields are indexed
- **Progress Updates**: Updates every 5,000 processed records
- **Memory Management**: Files are processed in chunks to avoid memory issues

## Limitations (Free Tier)

On Render's free tier:
- **0.1 CPU**: Shared between web and worker processes
- **512MB RAM**: Sufficient for most use cases
- **Spin-down**: Service spins down after 15 minutes of inactivity
- **Cold Start**: First request after spin-down may take 30-60 seconds

For production workloads, consider upgrading to a paid tier for better performance.

## Development

### Running Tests

```bash
python manage.py test
```

### Code Style

- No comments (self-documenting code)
- Functions under 200 lines
- Descriptive variable and function names
- All imports at the top of files

### Project Architecture

- **Handlers**: Business logic separated into handler classes
- **DBIO**: Database I/O operations abstracted
- **Base App**: Reusable components for common functionality
- **Soft Delete**: Products are soft-deleted (state-based) rather than physically removed

## Troubleshooting

### Celery Not Connecting to Redis

- Ensure Redis is running: `redis-cli ping`
- Check Redis URL format (use `rediss://` for TLS)
- Verify SSL certificate requirements are set correctly

### CSV Import Fails

- Check file format (must have `sku`, `name` columns)
- Verify file size (max 100MB)
- Check Celery worker logs for errors
- Ensure file path is accessible to Celery worker

### Static Files Not Loading

- Run `python manage.py collectstatic`
- Ensure WhiteNoise middleware is enabled
- Check `STATIC_ROOT` and `STATIC_URL` settings

## License

This project is part of a technical assignment.

## Author

Built as a scalable product import system demonstrating:
- Django best practices
- Asynchronous task processing
- Real-time progress tracking
- Webhook integrations
- Clean, maintainable code architecture

