export type ItemCategory = 
  | 'ID Card'
  | 'Electronics'
  | 'Books'
  | 'Keys'
  | 'Bags'
  | 'Accessories'
  | 'Other';

export type ItemStatus = 'Lost' | 'Found' | 'Returned';

export interface LostAndFoundItem {
  itemId: string;
  itemName: string;
  category: ItemCategory;
  description: string;
  rfidTagId: string;
  locationFound: string;
  dateReported: string;
  reportedBy: string;
  contactInformation: string;
  status: ItemStatus;
  checkInTime: string | null;
  checkOutTime: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ItemStats {
  totalItems: number;
  lostItems: number;
  foundItems: number;
  returnedItems: number;
  categoryCounts?: Record<string, number>;
}

export interface CreateItemInput {
  itemName: string;
  category: ItemCategory;
  description: string;
  rfidTagId: string;
  locationFound: string;
  dateReported: string;
  reportedBy: string;
  contactInformation: string;
  status: ItemStatus;
}

export interface UpdateItemInput {
  itemName?: string;
  category?: ItemCategory;
  description?: string;
  rfidTagId?: string;
  locationFound?: string;
  dateReported?: string;
  reportedBy?: string;
  contactInformation?: string;
  status?: ItemStatus;
  checkInTime?: string | null;
  checkOutTime?: string | null;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export type NavigationPage = 
  | 'dashboard'
  | 'all-items'
  | 'register'
  | 'lost-items'
  | 'found-items'
  | 'returned-items'
  | 'settings';
