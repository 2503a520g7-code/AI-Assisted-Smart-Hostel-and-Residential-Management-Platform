import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import {
  DynamoDBDocumentClient,
  ScanCommand,
  GetCommand,
  PutCommand,
  DeleteCommand,
  UpdateCommand,
} from '@aws-sdk/lib-dynamodb';

// Initialize DynamoDB Client with environment configuration
const region = process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || 'us-east-1';
const client = new DynamoDBClient({ region });
const ddbDocClient = DynamoDBDocumentClient.from(client, {
  marshallOptions: {
    removeUndefinedValues: true,
  },
});

const TABLE_NAME = process.env.ITEMS_TABLE_NAME || process.env.TABLE_NAME || 'CampusLostAndFoundItems';

/**
 * Standard CORS Response Headers
 */
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
  'Access-Control-Allow-Methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
  'Content-Type': 'application/json',
};

/**
 * Helper to build standard JSON response
 */
function buildResponse(statusCode, body) {
  return {
    statusCode,
    headers: CORS_HEADERS,
    body: JSON.stringify(body),
  };
}

/**
 * Normalize HTTP method and path for both REST API and HTTP API v2
 */
function extractRequestDetails(event) {
  const method = (
    event.httpMethod ||
    event.requestContext?.http?.method ||
    'GET'
  ).toUpperCase();

  const path =
    event.path ||
    event.rawPath ||
    event.requestContext?.http?.path ||
    '/';

  const pathParameters = event.pathParameters || {};
  const queryStringParameters = event.queryStringParameters || {};
  let body = {};

  if (event.body) {
    try {
      body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    } catch (e) {
      console.warn('Failed to parse event body as JSON:', e);
      body = {};
    }
  }

  return { method, path, pathParameters, queryStringParameters, body };
}

/**
 * AWS Lambda Handler
 */
export const handler = async (event) => {
  console.log('Received event:', JSON.stringify(event, null, 2));

  const { method, path, pathParameters, queryStringParameters, body } = extractRequestDetails(event);

  // Handle CORS preflight
  if (method === 'OPTIONS') {
    return buildResponse(200, { message: 'Preflight OK' });
  }

  try {
    // 1. GET /stats - Dashboard statistics aggregated from DynamoDB
    if (method === 'GET' && (path.endsWith('/stats') || path === '/stats')) {
      return await handleGetStats();
    }

    // 2. PATCH /items/{itemId}/status - Smart Box check-in/check-out and status update
    if (method === 'PATCH' && (path.includes('/status') || pathParameters.proxy?.includes('/status'))) {
      const itemId = pathParameters.itemId || extractItemIdFromPath(path);
      return await handlePatchStatus(itemId, body);
    }

    // 3. GET /items/{itemId} - Single item retrieval
    // 4. PUT /items/{itemId} - Update item
    // 5. DELETE /items/{itemId} - Delete item
    const singleItemId = pathParameters.itemId || extractItemIdFromPath(path);
    if (singleItemId && singleItemId !== 'items' && singleItemId !== 'stats') {
      if (method === 'GET') {
        return await handleGetItem(singleItemId);
      }
      if (method === 'PUT') {
        return await handleUpdateItem(singleItemId, body);
      }
      if (method === 'DELETE') {
        return await handleDeleteItem(singleItemId);
      }
    }

    // 6. GET /items - List items with optional filtering
    if (method === 'GET' && (path.endsWith('/items') || path === '/items' || path === '/')) {
      return await handleListItems(queryStringParameters);
    }

    // 7. POST /items - Register new item
    if (method === 'POST' && (path.endsWith('/items') || path === '/items' || path === '/')) {
      return await handleCreateItem(body);
    }

    // Route not found
    return buildResponse(404, {
      success: false,
      error: `Route not found: ${method} ${path}`,
    });
  } catch (error) {
    console.error('Unhandled Lambda error:', error);
    return buildResponse(500, {
      success: false,
      error: error.message || 'Internal Server Error',
    });
  }
};

/**
 * Extract itemId from URL path like /items/LF-12345
 */
function extractItemIdFromPath(path) {
  const parts = path.split('/').filter(Boolean);
  const itemsIndex = parts.indexOf('items');
  if (itemsIndex !== -1 && parts[itemsIndex + 1]) {
    return decodeURIComponent(parts[itemsIndex + 1]);
  }
  return null;
}

/**
 * 1. handleGetStats: Calculate live statistics directly from DynamoDB items
 */
async function handleGetStats() {
  const command = new ScanCommand({
    TableName: TABLE_NAME,
    ProjectionExpression: 'itemId, #status, category, createdAt',
    ExpressionAttributeNames: {
      '#status': 'status',
    },
  });

  const result = await ddbDocClient.send(command);
  const items = result.Items || [];

  let lostItems = 0;
  let foundItems = 0;
  let returnedItems = 0;
  const categoryCounts = {
    'ID Card': 0,
    'Electronics': 0,
    'Books': 0,
    'Keys': 0,
    'Bags': 0,
    'Accessories': 0,
    'Other': 0,
  };

  for (const item of items) {
    if (item.status === 'Lost') lostItems++;
    else if (item.status === 'Found') foundItems++;
    else if (item.status === 'Returned') returnedItems++;

    if (item.category) {
      categoryCounts[item.category] = (categoryCounts[item.category] || 0) + 1;
    }
  }

  const stats = {
    totalItems: items.length,
    lostItems,
    foundItems,
    returnedItems,
    categoryCounts,
    timestamp: new Date().toISOString(),
  };

  return buildResponse(200, {
    success: true,
    data: stats,
  });
}

/**
 * 2. handleListItems: Retrieve all items with optional filters
 */
async function handleListItems(queryParams = {}) {
  const command = new ScanCommand({
    TableName: TABLE_NAME,
  });

  const result = await ddbDocClient.send(command);
  let items = result.Items || [];

  // Filter in memory for scan efficiency or DynamoDB FilterExpression
  if (queryParams.status) {
    items = items.filter(
      (item) => item.status?.toLowerCase() === queryParams.status.toLowerCase()
    );
  }

  if (queryParams.category) {
    items = items.filter(
      (item) => item.category?.toLowerCase() === queryParams.category.toLowerCase()
    );
  }

  if (queryParams.search) {
    const q = queryParams.search.toLowerCase();
    items = items.filter(
      (item) =>
        item.itemName?.toLowerCase().includes(q) ||
        item.itemId?.toLowerCase().includes(q) ||
        item.rfidTagId?.toLowerCase().includes(q) ||
        item.description?.toLowerCase().includes(q) ||
        item.locationFound?.toLowerCase().includes(q)
    );
  }

  // Sort by createdAt descending
  items.sort((a, b) => new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime());

  return buildResponse(200, {
    success: true,
    data: items,
    count: items.length,
  });
}

/**
 * 3. handleGetItem: Retrieve single item by itemId
 */
async function handleGetItem(itemId) {
  if (!itemId) {
    return buildResponse(400, { success: false, error: 'Missing itemId parameter' });
  }

  const command = new GetCommand({
    TableName: TABLE_NAME,
    Key: { itemId },
  });

  const result = await ddbDocClient.send(command);
  if (!result.Item) {
    return buildResponse(404, { success: false, error: `Item with ID '${itemId}' not found` });
  }

  return buildResponse(200, {
    success: true,
    data: result.Item,
  });
}

/**
 * 4. handleCreateItem: Register new item
 */
async function handleCreateItem(body) {
  const {
    itemName,
    category,
    description = '',
    rfidTagId = '',
    locationFound = '',
    dateReported,
    reportedBy = '',
    contactInformation = '',
    status = 'Lost',
  } = body;

  // Validation
  if (!itemName || !category || !status) {
    return buildResponse(400, {
      success: false,
      error: 'Validation failed: itemName, category, and status are required fields.',
    });
  }

  const now = new Date().toISOString();
  // Generate itemId: e.g. LF-20261103-9A4B
  const randomSuffix = Math.random().toString(36).substring(2, 6).toUpperCase();
  const dateStr = now.slice(0, 10).replace(/-/g, '');
  const itemId = body.itemId || `LF-${dateStr}-${randomSuffix}`;

  const newItem = {
    itemId,
    itemName: itemName.trim(),
    category,
    description: description.trim(),
    rfidTagId: rfidTagId.trim().toUpperCase(),
    locationFound: locationFound.trim(),
    dateReported: dateReported || now.slice(0, 10),
    reportedBy: reportedBy.trim(),
    contactInformation: contactInformation.trim(),
    status,
    checkInTime: status === 'Found' ? now : null,
    checkOutTime: status === 'Returned' ? now : null,
    createdAt: now,
    updatedAt: now,
  };

  const command = new PutCommand({
    TableName: TABLE_NAME,
    Item: newItem,
  });

  await ddbDocClient.send(command);

  return buildResponse(201, {
    success: true,
    message: 'Item registered successfully in DynamoDB',
    data: newItem,
  });
}

/**
 * 5. handleUpdateItem: Update item details
 */
async function handleUpdateItem(itemId, body) {
  if (!itemId) {
    return buildResponse(400, { success: false, error: 'Missing itemId parameter' });
  }

  // Fetch current item first
  const getCommand = new GetCommand({
    TableName: TABLE_NAME,
    Key: { itemId },
  });
  const currentResult = await ddbDocClient.send(getCommand);
  if (!currentResult.Item) {
    return buildResponse(404, { success: false, error: `Item with ID '${itemId}' not found` });
  }

  const currentItem = currentResult.Item;
  const now = new Date().toISOString();

  // Prepare updated item
  const updatedItem = {
    ...currentItem,
    itemName: body.itemName !== undefined ? body.itemName.trim() : currentItem.itemName,
    category: body.category || currentItem.category,
    description: body.description !== undefined ? body.description.trim() : currentItem.description,
    rfidTagId: body.rfidTagId !== undefined ? body.rfidTagId.trim().toUpperCase() : currentItem.rfidTagId,
    locationFound: body.locationFound !== undefined ? body.locationFound.trim() : currentItem.locationFound,
    dateReported: body.dateReported || currentItem.dateReported,
    reportedBy: body.reportedBy !== undefined ? body.reportedBy.trim() : currentItem.reportedBy,
    contactInformation: body.contactInformation !== undefined ? body.contactInformation.trim() : currentItem.contactInformation,
    status: body.status || currentItem.status,
    checkInTime: body.checkInTime !== undefined ? body.checkInTime : currentItem.checkInTime,
    checkOutTime: body.checkOutTime !== undefined ? body.checkOutTime : currentItem.checkOutTime,
    updatedAt: now,
  };

  const putCommand = new PutCommand({
    TableName: TABLE_NAME,
    Item: updatedItem,
  });

  await ddbDocClient.send(putCommand);

  return buildResponse(200, {
    success: true,
    message: 'Item updated successfully in DynamoDB',
    data: updatedItem,
  });
}

/**
 * 6. handlePatchStatus: Update item status (Smart Box Check In / Check Out)
 */
async function handlePatchStatus(itemId, body) {
  if (!itemId) {
    return buildResponse(400, { success: false, error: 'Missing itemId parameter' });
  }

  const { status, checkInTime, checkOutTime } = body;
  if (!status || !['Lost', 'Found', 'Returned'].includes(status)) {
    return buildResponse(400, {
      success: false,
      error: "Valid status ('Lost' | 'Found' | 'Returned') is required.",
    });
  }

  // Retrieve current item
  const getCommand = new GetCommand({
    TableName: TABLE_NAME,
    Key: { itemId },
  });
  const currentResult = await ddbDocClient.send(getCommand);
  if (!currentResult.Item) {
    return buildResponse(404, { success: false, error: `Item with ID '${itemId}' not found` });
  }

  const now = new Date().toISOString();
  let newCheckInTime = currentResult.Item.checkInTime || null;
  let newCheckOutTime = currentResult.Item.checkOutTime || null;

  // Smart Box logic:
  // Check In -> Set status to Found, record check-in time
  // Check Out -> Set status to Returned, record check-out time
  // Mark as Lost -> Set status to Lost
  if (status === 'Found') {
    newCheckInTime = checkInTime || now;
  } else if (status === 'Returned') {
    newCheckOutTime = checkOutTime || now;
  }

  const updateCommand = new UpdateCommand({
    TableName: TABLE_NAME,
    Key: { itemId },
    UpdateExpression: 'SET #status = :s, checkInTime = :cin, checkOutTime = :cout, updatedAt = :u',
    ExpressionAttributeNames: {
      '#status': 'status',
    },
    ExpressionAttributeValues: {
      ':s': status,
      ':cin': newCheckInTime,
      ':cout': newCheckOutTime,
      ':u': now,
    },
    ReturnValues: 'ALL_NEW',
  });

  const updateResult = await ddbDocClient.send(updateCommand);

  return buildResponse(200, {
    success: true,
    message: `Item status updated to '${status}' successfully in DynamoDB`,
    data: updateResult.Attributes,
  });
}

/**
 * 7. handleDeleteItem: Remove item from DynamoDB
 */
async function handleDeleteItem(itemId) {
  if (!itemId) {
    return buildResponse(400, { success: false, error: 'Missing itemId parameter' });
  }

  const command = new DeleteCommand({
    TableName: TABLE_NAME,
    Key: { itemId },
  });

  await ddbDocClient.send(command);

  return buildResponse(200, {
    success: true,
    message: `Item '${itemId}' deleted successfully from DynamoDB`,
    itemId,
  });
}
