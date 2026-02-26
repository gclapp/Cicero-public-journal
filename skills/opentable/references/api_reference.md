# OpenTable API Reference

## Authentication

All requests require a Bearer token in the Authorization header:
```
Authorization: Bearer {api_key}
```

## Endpoints

### Search Restaurants
```
GET /v2/restaurants
```

**Parameters:**
- `city` (string) - City name
- `cuisine` (string) - Cuisine type
- `name` (string) - Restaurant name search
- `price` (int) - Price level 1-4 ($ to $$$$)
- `lat` (float) - Latitude
- `lng` (float) - Longitude
- `radius` (int) - Search radius in meters (default: 5000)
- `date` (string) - Date for availability (YYYY-MM-DD)
- `time` (string) - Time for availability (HH:MM)
- `party_size` (int) - Party size
- `available_only` (boolean) - Only return restaurants with availability
- `limit` (int) - Max results (default: 25)
- `offset` (int) - Pagination offset

**Response:**
```json
{
  "total": 150,
  "restaurants": [
    {
      "id": 12345,
      "name": "Restaurant Name",
      "address": "123 Main St",
      "city": "Portland",
      "state": "OR",
      "phone": "503-555-0123",
      "cuisine": "Italian",
      "price": 3,
      "rating": 4.5,
      "review_count": 234,
      "reserve_url": "https://...",
      "image_url": "https://...",
      "distance": 1200
    }
  ]
}
```

### Get Restaurant Details
```
GET /v2/restaurants/{id}
```

**Response:**
```json
{
  "id": 12345,
  "name": "Restaurant Name",
  "description": "...",
  "address": "123 Main St",
  "city": "Portland",
  "state": "OR",
  "postal_code": "97201",
  "country": "US",
  "phone": "503-555-0123",
  "website": "https://...",
  "cuisine": "Italian",
  "price": 3,
  "rating": 4.5,
  "review_count": 234,
  "hours": {...},
  "dress_code": "Business Casual",
  "parking": "Valet",
  "payment_options": ["Visa", "MasterCard"],
  "reserve_url": "https://...",
  "image_url": "https://...",
  "lat": 45.5231,
  "lng": -122.6765
}
```

### Check Availability
```
GET /v2/restaurants/{id}/availability
```

**Parameters:**
- `date` (string, required) - YYYY-MM-DD
- `time` (string, required) - HH:MM (24-hour)
- `party_size` (int, required)

**Response:**
```json
{
  "available": true,
  "times": ["18:00", "18:30", "19:00", "19:30"],
  "message": ""
}
```

### Make Reservation
```
POST /v2/reservations
```

**Body:**
```json
{
  "restaurant_id": 12345,
  "date": "2026-02-27",
  "time": "19:00",
  "party_size": 4,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "503-555-0123",
  "special_requests": "Anniversary dinner"
}
```

**Response:**
```json
{
  "confirmation_number": "OT12345678",
  "restaurant_name": "Restaurant Name",
  "date": "2026-02-27",
  "time": "19:00",
  "party_size": 4,
  "status": "confirmed",
  "cancellation_url": "https://...",
  "share_url": "https://..."
}
```

### Get Reservation
```
GET /v2/reservations/{confirmation_number}
```

**Response:**
```json
{
  "confirmation_number": "OT12345678",
  "restaurant_name": "Restaurant Name",
  "restaurant_id": 12345,
  "date": "2026-02-27",
  "time": "19:00",
  "party_size": 4,
  "status": "confirmed",
  "diner_first_name": "John",
  "diner_last_name": "Doe",
  "diner_email": "john@example.com",
  "diner_phone": "503-555-0123",
  "special_requests": "Anniversary dinner",
  "share_url": "https://...",
  "cancellation_url": "https://...",
  "created_at": "2026-02-25T10:30:00Z"
}
```

### List Reservations
```
GET /v2/reservations
```

**Parameters:**
- `email` (string) - Filter by diner email
- `confirmation_number` (string) - Lookup specific reservation
- `upcoming_only` (boolean) - Only return future reservations (default: true)

**Response:**
```json
{
  "reservations": [
    {
      "confirmation_number": "OT12345678",
      "restaurant_name": "Restaurant Name",
      "restaurant_id": 12345,
      "date": "2026-02-27",
      "time": "19:00",
      "party_size": 4,
      "status": "confirmed",
      "created_at": "2026-02-25T10:30:00Z"
    }
  ]
}
```

### Cancel Reservation
```
POST /v2/reservations/{confirmation_number}/cancel
```

**Body:**
```json
{
  "email": "john@example.com",
  "reason": "Change of plans"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Reservation cancelled successfully",
  "confirmation_number": "OT12345678",
  "refund_info": {
    "refundable": true,
    "refund_amount": 0.00
  },
  "cancellation_policy": "Free cancellation up to 24 hours before reservation"
}
```

## Error Codes

- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid API key)
- `403` - Forbidden (not authorized to access resource)
- `404` - Not Found (reservation or restaurant not found)
- `409` - Conflict (reservation already cancelled or time unavailable)
- `422` - Unprocessable Entity (validation error)
- `429` - Rate Limited
- `500` - Server Error

## Rate Limits

- 100 requests per minute for standard partners
- Contact OpenTable for increased limits
