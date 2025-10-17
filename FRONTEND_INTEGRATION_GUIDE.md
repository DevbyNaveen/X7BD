# Food QR Frontend Integration Guide

## 🚀 Ready for Frontend Integration!

Your Food QR backend is **100% ready** for frontend integration. Here's everything you need to connect your frontend application.

## 📡 API Base URL
```
http://localhost:8060/api/v1/food
```

## 🔑 Your Business ID
```
fd8a3d59-4a06-43c2-9820-0e3222867117
```

## 📋 Available API Endpoints

### QR Code Generation
```javascript
// Generate single QR code
POST /api/v1/food/qr/generate
{
  "type": "menu_item",
  "target_id": "uuid",
  "business_id": "fd8a3d59-4a06-43c2-9820-0e3222867117",
  "size": 200,
  "format": "png"
}

// Generate multiple QR codes
POST /api/v1/food/qr/bulk-generate?business_id=fd8a3d59-4a06-43c2-9820-0e3222867117&qr_type=menu_item&target_ids=uuid1,uuid2,uuid3&size=200&format=png

// Get QR code image
GET /api/v1/food/qr/image/{qr_id}
```

### QR Code Scanning
```javascript
// Scan QR code
POST /api/v1/food/qr/scan
{
  "qr_data": "https://app.example.com/food/menu_item/item-123",
  "scanner_location": "restaurant_floor",
  "scanner_id": "scanner_001"
}
```

### Food Items
```javascript
// Create food item with QR
POST /api/v1/food/items?generate_qr=true
{
  "business_id": "fd8a3d59-4a06-43c2-9820-0e3222867117",
  "name": "Margherita Pizza",
  "description": "Classic tomato and mozzarella pizza",
  "price": 14.99,
  "cost": 6.50,
  "is_available": true,
  "prep_time": 15,
  "calories": 350,
  "allergens": ["gluten", "dairy"],
  "tags": ["vegetarian", "classic", "popular"]
}

// Get item QR code
GET /api/v1/food/items/{item_id}/qr
```

### Analytics
```javascript
// Get QR analytics
GET /api/v1/food/qr/analytics/fd8a3d59-4a06-43c2-9820-0e3222867117?period=7d&qr_type=menu_item

// Get popular QR codes
GET /api/v1/food/qr/popular/fd8a3d59-4a06-43c2-9820-0e3222867117?limit=10&period=7d
```

## 🎯 Frontend Integration Examples

### React/JavaScript Example
```javascript
class FoodQRService {
  constructor(baseURL = 'http://localhost:8060/api/v1/food') {
    this.baseURL = baseURL;
    this.businessId = 'fd8a3d59-4a06-43c2-9820-0e3222867117';
  }

  // Generate QR code for menu item
  async generateMenuItemQR(itemId, size = 200) {
    const response = await fetch(`${this.baseURL}/qr/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: 'menu_item',
        target_id: itemId,
        business_id: this.businessId,
        size: size,
        format: 'png'
      })
    });
    
    return await response.json();
  }

  // Generate QR code for table
  async generateTableQR(tableNumber, capacity = 4) {
    const response = await fetch(`${this.baseURL}/qr/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: 'table',
        target_id: crypto.randomUUID(),
        business_id: this.businessId,
        size: 250,
        format: 'png',
        custom_data: {
          table_number: tableNumber,
          capacity: capacity
        }
      })
    });
    
    return await response.json();
  }

  // Scan QR code
  async scanQRCode(qrData, scannerLocation = 'frontend') {
    const response = await fetch(`${this.baseURL}/qr/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        qr_data: qrData,
        scanner_location: scannerLocation,
        scanner_id: 'web_scanner'
      })
    });
    
    return await response.json();
  }

  // Create food item with QR
  async createFoodItemWithQR(itemData) {
    const response = await fetch(`${this.baseURL}/items?generate_qr=true`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...itemData,
        business_id: this.businessId
      })
    });
    
    return await response.json();
  }

  // Get QR analytics
  async getQRAnalytics(period = '7d') {
    const response = await fetch(
      `${this.baseURL}/qr/analytics/${this.businessId}?period=${period}`
    );
    
    return await response.json();
  }
}

// Usage example
const qrService = new FoodQRService();

// Generate QR for menu item
const qrCode = await qrService.generateMenuItemQR('item-123');
console.log('QR Code:', qrCode.qr_id);

// Display QR code image
const qrImage = document.createElement('img');
qrImage.src = `data:image/png;base64,${qrCode.qr_data}`;
document.body.appendChild(qrImage);
```

### Vue.js Example
```vue
<template>
  <div class="qr-generator">
    <h2>Food QR Code Generator</h2>
    
    <!-- Menu Item QR -->
    <div class="qr-section">
      <h3>Menu Item QR Code</h3>
      <input v-model="menuItemId" placeholder="Menu Item ID" />
      <button @click="generateMenuItemQR">Generate QR</button>
      <img v-if="menuItemQR" :src="`data:image/png;base64,${menuItemQR.qr_data}`" />
    </div>

    <!-- Table QR -->
    <div class="qr-section">
      <h3>Table QR Code</h3>
      <input v-model="tableNumber" placeholder="Table Number" />
      <button @click="generateTableQR">Generate QR</button>
      <img v-if="tableQR" :src="`data:image/png;base64,${tableQR.qr_data}`" />
    </div>

    <!-- QR Scanner -->
    <div class="qr-section">
      <h3>QR Code Scanner</h3>
      <input v-model="qrData" placeholder="QR Code Data" />
      <button @click="scanQRCode">Scan QR</button>
      <div v-if="scanResult">
        <p>Valid: {{ scanResult.valid }}</p>
        <p>Action URL: {{ scanResult.action_url }}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      businessId: 'fd8a3d59-4a06-43c2-9820-0e3222867117',
      baseURL: 'http://localhost:8060/api/v1/food',
      menuItemId: '',
      tableNumber: '',
      qrData: '',
      menuItemQR: null,
      tableQR: null,
      scanResult: null
    }
  },
  methods: {
    async generateMenuItemQR() {
      try {
        const response = await fetch(`${this.baseURL}/qr/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'menu_item',
            target_id: this.menuItemId,
            business_id: this.businessId,
            size: 200,
            format: 'png'
          })
        });
        this.menuItemQR = await response.json();
      } catch (error) {
        console.error('Error generating menu item QR:', error);
      }
    },

    async generateTableQR() {
      try {
        const response = await fetch(`${this.baseURL}/qr/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'table',
            target_id: crypto.randomUUID(),
            business_id: this.businessId,
            size: 250,
            format: 'png',
            custom_data: {
              table_number: this.tableNumber,
              capacity: 4
            }
          })
        });
        this.tableQR = await response.json();
      } catch (error) {
        console.error('Error generating table QR:', error);
      }
    },

    async scanQRCode() {
      try {
        const response = await fetch(`${this.baseURL}/qr/scan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            qr_data: this.qrData,
            scanner_location: 'vue_frontend',
            scanner_id: 'web_scanner'
          })
        });
        this.scanResult = await response.json();
      } catch (error) {
        console.error('Error scanning QR:', error);
      }
    }
  }
}
</script>
```

### Angular Example
```typescript
// food-qr.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class FoodQRService {
  private baseURL = 'http://localhost:8060/api/v1/food';
  private businessId = 'fd8a3d59-4a06-43c2-9820-0e3222867117';

  constructor(private http: HttpClient) {}

  generateMenuItemQR(itemId: string, size: number = 200): Observable<any> {
    return this.http.post(`${this.baseURL}/qr/generate`, {
      type: 'menu_item',
      target_id: itemId,
      business_id: this.businessId,
      size: size,
      format: 'png'
    });
  }

  generateTableQR(tableNumber: string, capacity: number = 4): Observable<any> {
    return this.http.post(`${this.baseURL}/qr/generate`, {
      type: 'table',
      target_id: crypto.randomUUID(),
      business_id: this.businessId,
      size: 250,
      format: 'png',
      custom_data: {
        table_number: tableNumber,
        capacity: capacity
      }
    });
  }

  scanQRCode(qrData: string, scannerLocation: string = 'angular_frontend'): Observable<any> {
    return this.http.post(`${this.baseURL}/qr/scan`, {
      qr_data: qrData,
      scanner_location: scannerLocation,
      scanner_id: 'web_scanner'
    });
  }

  getQRAnalytics(period: string = '7d'): Observable<any> {
    return this.http.get(`${this.baseURL}/qr/analytics/${this.businessId}?period=${period}`);
  }
}

// qr-generator.component.ts
import { Component } from '@angular/core';
import { FoodQRService } from './food-qr.service';

@Component({
  selector: 'app-qr-generator',
  template: `
    <div class="qr-generator">
      <h2>Food QR Code Generator</h2>
      
      <div class="qr-section">
        <h3>Menu Item QR Code</h3>
        <input [(ngModel)]="menuItemId" placeholder="Menu Item ID" />
        <button (click)="generateMenuItemQR()">Generate QR</button>
        <img *ngIf="menuItemQR" [src]="'data:image/png;base64,' + menuItemQR.qr_data" />
      </div>

      <div class="qr-section">
        <h3>Table QR Code</h3>
        <input [(ngModel)]="tableNumber" placeholder="Table Number" />
        <button (click)="generateTableQR()">Generate QR</button>
        <img *ngIf="tableQR" [src]="'data:image/png;base64,' + tableQR.qr_data" />
      </div>
    </div>
  `
})
export class QRGeneratorComponent {
  menuItemId = '';
  tableNumber = '';
  menuItemQR: any = null;
  tableQR: any = null;

  constructor(private qrService: FoodQRService) {}

  generateMenuItemQR() {
    this.qrService.generateMenuItemQR(this.menuItemId).subscribe({
      next: (response) => {
        this.menuItemQR = response;
        console.log('Menu Item QR generated:', response.qr_id);
      },
      error: (error) => console.error('Error:', error)
    });
  }

  generateTableQR() {
    this.qrService.generateTableQR(this.tableNumber).subscribe({
      next: (response) => {
        this.tableQR = response;
        console.log('Table QR generated:', response.qr_id);
      },
      error: (error) => console.error('Error:', error)
    });
  }
}
```

## 📱 Mobile Integration

### React Native Example
```javascript
import React, { useState } from 'react';
import { View, Text, TextInput, Button, Image, Alert } from 'react-native';

const FoodQRService = {
  baseURL: 'http://localhost:8060/api/v1/food',
  businessId: 'fd8a3d59-4a06-43c2-9820-0e3222867117',

  async generateQR(type, targetId, customData = {}) {
    const response = await fetch(`${this.baseURL}/qr/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type,
        target_id: targetId,
        business_id: this.businessId,
        size: 200,
        format: 'png',
        custom_data: customData
      })
    });
    return await response.json();
  },

  async scanQR(qrData) {
    const response = await fetch(`${this.baseURL}/qr/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        qr_data: qrData,
        scanner_location: 'mobile_app',
        scanner_id: 'react_native_scanner'
      })
    });
    return await response.json();
  }
};

const QRGenerator = () => {
  const [menuItemId, setMenuItemId] = useState('');
  const [qrCode, setQrCode] = useState(null);

  const generateQR = async () => {
    try {
      const result = await FoodQRService.generateQR('menu_item', menuItemId);
      setQrCode(result);
    } catch (error) {
      Alert.alert('Error', 'Failed to generate QR code');
    }
  };

  return (
    <View style={{ padding: 20 }}>
      <Text>Food QR Generator</Text>
      <TextInput
        value={menuItemId}
        onChangeText={setMenuItemId}
        placeholder="Menu Item ID"
        style={{ borderWidth: 1, padding: 10, margin: 10 }}
      />
      <Button title="Generate QR" onPress={generateQR} />
      {qrCode && (
        <Image
          source={{ uri: `data:image/png;base64,${qrCode.qr_data}` }}
          style={{ width: 200, height: 200, margin: 20 }}
        />
      )}
    </View>
  );
};

export default QRGenerator;
```

## 🔧 Configuration

### Environment Variables for Frontend
```javascript
// config.js
export const config = {
  API_BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8060/api/v1/food',
  BUSINESS_ID: 'fd8a3d59-4a06-43c2-9820-0e3222867117',
  QR_DEFAULT_SIZE: 200,
  QR_DEFAULT_FORMAT: 'png'
};
```

### CORS Configuration
Your backend already has CORS enabled for all origins, so frontend integration should work seamlessly.

## 🚀 Getting Started

### 1. Start Your Backend Server
```bash
python -m app.main
```

### 2. Test API Endpoints
```bash
# Test health endpoint
curl http://localhost:8060/health

# Test QR generation
curl -X POST http://localhost:8060/api/v1/food/qr/generate \
  -H "Content-Type: application/json" \
  -d '{
    "type": "menu_item",
    "target_id": "test-item-123",
    "business_id": "fd8a3d59-4a06-43c2-9820-0e3222867117",
    "size": 200,
    "format": "png"
  }'
```

### 3. Access API Documentation
Visit: `http://localhost:8060/docs`

## 📊 Real-time Features

### WebSocket Integration (if needed)
```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8060/ws');

ws.onopen = () => {
  console.log('Connected to Food QR WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};
```

## 🎯 Production Deployment

### Frontend Build Configuration
```javascript
// webpack.config.js or vite.config.js
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8060',
        changeOrigin: true
      }
    }
  }
};
```

### Docker Configuration
```dockerfile
# Dockerfile for frontend
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🎉 You're Ready!

Your Food QR backend is **100% ready** for frontend integration! The API is fully functional, CORS is enabled, and all endpoints are working perfectly.

**Next Steps:**
1. Choose your frontend framework (React, Vue, Angular, etc.)
2. Use the provided examples above
3. Start building your QR-enabled food application
4. Test with your business ID: `fd8a3d59-4a06-43c2-9820-0e3222867117`

Your Food QR system is ready to revolutionize your restaurant's digital experience! 🍽️📱
