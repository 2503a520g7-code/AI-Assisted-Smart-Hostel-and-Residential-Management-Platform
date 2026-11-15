/**
 * Local Development Server for testing Campus Lost & Found API
 * Emulates AWS API Gateway + Lambda locally without external dependencies.
 */
import http from 'http';
import { handler } from './index.js';

const PORT = process.env.PORT || 5000;

// In-memory items store for when AWS credentials are not configured locally
let inMemoryItems = [
  {
    itemId: 'LF-20261103-7K9P',
    itemName: 'Student ID Card - Harshitha M.',
    category: 'ID Card',
    description: 'Blue university lanyard with magnetic student access card and library barcode.',
    rfidTagId: 'RFID-981244',
    locationFound: 'Main Campus Library 2nd Floor',
    dateReported: '2026-11-02',
    reportedBy: 'Security Officer Robert',
    contactInformation: 'security@campus.edu / Ext 4410',
    status: 'Found',
    checkInTime: '2026-11-02T10:15:00.000Z',
    checkOutTime: null,
    createdAt: '2026-11-02T10:15:00.000Z',
    updatedAt: '2026-11-02T10:15:00.000Z',
  },
  {
    itemId: 'LF-20261103-3M8X',
    itemName: 'MacBook Air M2 Space Gray',
    category: 'Electronics',
    description: 'Space Gray 13-inch laptop with stickers: NASA and Python. Found in Lecture Hall B.',
    rfidTagId: 'RFID-441908',
    locationFound: 'Engineering Building - Lecture Hall B',
    dateReported: '2026-11-01',
    reportedBy: 'Prof. S. Venkatesh',
    contactInformation: 's.venkatesh@campus.edu',
    status: 'Lost',
    checkInTime: null,
    checkOutTime: null,
    createdAt: '2026-11-01T14:30:00.000Z',
    updatedAt: '2026-11-01T14:30:00.000Z',
  },
  {
    itemId: 'LF-20261028-1W4C',
    itemName: 'Cloud Computing & Distributed Systems Textbook',
    category: 'Books',
    description: 'Hardcover edition with highlighted chapters 4 and 7. Left on cafeteria bench.',
    rfidTagId: 'RFID-112390',
    locationFound: 'Student Center Cafeteria',
    dateReported: '2026-10-28',
    reportedBy: 'Ananya Sharma',
    contactInformation: 'asharma@student.campus.edu',
    status: 'Returned',
    checkInTime: '2026-10-28T16:00:00.000Z',
    checkOutTime: '2026-10-29T11:20:00.000Z',
    createdAt: '2026-10-28T16:00:00.000Z',
    updatedAt: '2026-10-29T11:20:00.000Z',
  },
  {
    itemId: 'LF-20261025-5B2L',
    itemName: 'Set of 4 Brass Keys with Toyota Fob',
    category: 'Keys',
    description: 'Black braided keychain with 4 house keys and a black Toyota car remote.',
    rfidTagId: 'RFID-552910',
    locationFound: 'North Parking Lot Lot-C',
    dateReported: '2026-10-25',
    reportedBy: 'Grounds Maintenance Staff',
    contactInformation: 'maintenance@campus.edu',
    status: 'Found',
    checkInTime: '2026-10-25T09:40:00.000Z',
    checkOutTime: null,
    createdAt: '2026-10-25T09:40:00.000Z',
    updatedAt: '2026-10-25T09:40:00.000Z',
  },
  {
    itemId: 'LF-20261022-8Y6Z',
    itemName: 'Black Herschel Backpack',
    category: 'Bags',
    description: 'Contains notebook, scientific calculator TI-84, and water bottle.',
    rfidTagId: 'RFID-338190',
    locationFound: 'Sports Complex Bleachers',
    dateReported: '2026-10-22',
    reportedBy: 'Coach Davis',
    contactInformation: 'athletics@campus.edu',
    status: 'Lost',
    checkInTime: null,
    checkOutTime: null,
    createdAt: '2026-10-22T18:00:00.000Z',
    updatedAt: '2026-10-22T18:00:00.000Z',
  }
];

const server = http.createServer(async (req, res) => {
  // CORS Preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(200, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
    });
    return res.end();
  }

  // Parse URL and Query parameters
  const parsedUrl = new URL(req.url, `http://${req.headers.host}`);
  const pathname = parsedUrl.pathname;
  const queryParams = Object.fromEntries(parsedUrl.searchParams.entries());

  // Collect request body
  let bodyBuffer = '';
  req.on('data', (chunk) => {
    bodyBuffer += chunk;
  });

  req.on('end', async () => {
    // Check if we should route to real Lambda handler or local simulator
    const useAwsDynamo = process.env.AWS_ACCESS_KEY_ID || process.env.AWS_PROFILE;

    if (useAwsDynamo) {
      // Build API Gateway event
      const event = {
        httpMethod: req.method,
        path: pathname,
        queryStringParameters: queryParams,
        body: bodyBuffer || null,
        headers: req.headers,
      };

      try {
        const lambdaResult = await handler(event);
        res.writeHead(lambdaResult.statusCode, lambdaResult.headers);
        res.end(lambdaResult.body);
        return;
      } catch (err) {
        console.error('Lambda error:', err);
        res.writeHead(500, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        return res.end(JSON.stringify({ success: false, error: err.message }));
      }
    }

    // Local Mock Mode when no AWS credentials are provided locally
    console.log(`[Local Mock API] ${req.method} ${pathname}`);
    const sendJson = (status, data) => {
      res.writeHead(status, {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
      });
      res.end(JSON.stringify(data));
    };

    let parsedBody = {};
    if (bodyBuffer) {
      try {
        parsedBody = JSON.parse(bodyBuffer);
      } catch (e) {
        parsedBody = {};
      }
    }

    // 1. GET /stats
    if (req.method === 'GET' && pathname === '/stats') {
      let lost = 0, found = 0, returned = 0;
      const categoryCounts = {
        'ID Card': 0, 'Electronics': 0, 'Books': 0, 'Keys': 0, 'Bags': 0, 'Accessories': 0, 'Other': 0
      };
      inMemoryItems.forEach(item => {
        if (item.status === 'Lost') lost++;
        else if (item.status === 'Found') found++;
        else if (item.status === 'Returned') returned++;
        if (item.category && categoryCounts[item.category] !== undefined) {
          categoryCounts[item.category]++;
        }
      });
      return sendJson(200, {
        success: true,
        data: {
          totalItems: inMemoryItems.length,
          lostItems: lost,
          foundItems: found,
          returnedItems: returned,
          categoryCounts,
          isMock: true
        }
      });
    }

    // 2. PATCH /items/:itemId/status
    const statusMatch = pathname.match(/^\/items\/([^/]+)\/status$/);
    if (req.method === 'PATCH' && statusMatch) {
      const itemId = decodeURIComponent(statusMatch[1]);
      const idx = inMemoryItems.findIndex(i => i.itemId === itemId);
      if (idx === -1) {
        return sendJson(404, { success: false, error: `Item '${itemId}' not found` });
      }
      const now = new Date().toISOString();
      const newStatus = parsedBody.status;
      if (newStatus === 'Found') {
        inMemoryItems[idx].checkInTime = parsedBody.checkInTime || now;
      } else if (newStatus === 'Returned') {
        inMemoryItems[idx].checkOutTime = parsedBody.checkOutTime || now;
      }
      inMemoryItems[idx].status = newStatus;
      inMemoryItems[idx].updatedAt = now;
      return sendJson(200, { success: true, message: `Status updated to ${newStatus}`, data: inMemoryItems[idx] });
    }

    // 3. GET /items/:itemId
    const itemMatch = pathname.match(/^\/items\/([^/]+)$/);
    if (req.method === 'GET' && itemMatch && itemMatch[1] !== 'stats') {
      const itemId = decodeURIComponent(itemMatch[1]);
      const item = inMemoryItems.find(i => i.itemId === itemId);
      if (!item) return sendJson(404, { success: false, error: `Item '${itemId}' not found` });
      return sendJson(200, { success: true, data: item });
    }

    // 4. PUT /items/:itemId
    if (req.method === 'PUT' && itemMatch) {
      const itemId = decodeURIComponent(itemMatch[1]);
      const idx = inMemoryItems.findIndex(i => i.itemId === itemId);
      if (idx === -1) return sendJson(404, { success: false, error: `Item '${itemId}' not found` });
      const now = new Date().toISOString();
      inMemoryItems[idx] = { ...inMemoryItems[idx], ...parsedBody, updatedAt: now };
      return sendJson(200, { success: true, message: 'Item updated successfully', data: inMemoryItems[idx] });
    }

    // 5. DELETE /items/:itemId
    if (req.method === 'DELETE' && itemMatch) {
      const itemId = decodeURIComponent(itemMatch[1]);
      const idx = inMemoryItems.findIndex(i => i.itemId === itemId);
      if (idx === -1) return sendJson(404, { success: false, error: `Item '${itemId}' not found` });
      inMemoryItems.splice(idx, 1);
      return sendJson(200, { success: true, message: `Item ${itemId} deleted successfully`, itemId });
    }

    // 6. GET /items
    if (req.method === 'GET' && pathname === '/items') {
      let items = [...inMemoryItems];
      if (queryParams.status) {
        items = items.filter(i => i.status.toLowerCase() === queryParams.status.toLowerCase());
      }
      if (queryParams.category) {
        items = items.filter(i => i.category.toLowerCase() === queryParams.category.toLowerCase());
      }
      if (queryParams.search) {
        const q = queryParams.search.toLowerCase();
        items = items.filter(i => 
          i.itemName.toLowerCase().includes(q) ||
          i.itemId.toLowerCase().includes(q) ||
          i.rfidTagId.toLowerCase().includes(q) ||
          i.description.toLowerCase().includes(q) ||
          i.locationFound.toLowerCase().includes(q)
        );
      }
      return sendJson(200, { success: true, data: items, count: items.length });
    }

    // 7. POST /items
    if (req.method === 'POST' && pathname === '/items') {
      const now = new Date().toISOString();
      const randomSuffix = Math.random().toString(36).substring(2, 6).toUpperCase();
      const dateStr = now.slice(0, 10).replace(/-/g, '');
      const newItem = {
        itemId: parsedBody.itemId || `LF-${dateStr}-${randomSuffix}`,
        itemName: parsedBody.itemName,
        category: parsedBody.category,
        description: parsedBody.description || '',
        rfidTagId: (parsedBody.rfidTagId || '').toUpperCase(),
        locationFound: parsedBody.locationFound || '',
        dateReported: parsedBody.dateReported || now.slice(0, 10),
        reportedBy: parsedBody.reportedBy || '',
        contactInformation: parsedBody.contactInformation || '',
        status: parsedBody.status || 'Lost',
        checkInTime: parsedBody.status === 'Found' ? now : null,
        checkOutTime: parsedBody.status === 'Returned' ? now : null,
        createdAt: now,
        updatedAt: now,
      };
      inMemoryItems.unshift(newItem);
      return sendJson(201, { success: true, message: 'Item registered successfully', data: newItem });
    }

    return sendJson(404, { success: false, error: `Route not found: ${req.method} ${pathname}` });
  });
});

server.listen(PORT, () => {
  console.log(`=======================================================`);
  console.log(` Campus Lost & Found API Server Running on port ${PORT}`);
  console.log(` Endpoint: http://localhost:${PORT}`);
  console.log(` Emulating AWS API Gateway + Lambda endpoints`);
  console.log(`=======================================================`);
});
