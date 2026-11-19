import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { 
  LostAndFoundItem, 
  ItemStats, 
  ItemStatus, 
  NavigationPage, 
  CreateItemInput, 
  UpdateItemInput 
} from '../types/item';
import * as api from '../services/api';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
}

interface AppContextType {
  activePage: NavigationPage;
  setActivePage: (page: NavigationPage) => void;
  items: LostAndFoundItem[];
  stats: ItemStats | null;
  isLoading: boolean;
  isInitialLoad: boolean;
  error: string | null;
  awsStatus: 'connected' | 'not_configured' | 'error' | 'checking';
  awsStatusMessage: string;
  toasts: ToastMessage[];
  addToast: (type: ToastMessage['type'], message: string) => void;
  removeToast: (id: string) => void;
  refreshData: () => Promise<void>;
  createItem: (input: CreateItemInput) => Promise<LostAndFoundItem | null>;
  updateItem: (itemId: string, input: UpdateItemInput) => Promise<LostAndFoundItem | null>;
  updateStatus: (itemId: string, status: ItemStatus, extra?: { checkInTime?: string; checkOutTime?: string }) => Promise<boolean>;
  deleteItem: (itemId: string) => Promise<boolean>;
  selectedDetailItem: LostAndFoundItem | null;
  setSelectedDetailItem: (item: LostAndFoundItem | null) => void;
  selectedEditItem: LostAndFoundItem | null;
  setSelectedEditItem: (item: LostAndFoundItem | null) => void;
  selectedSmartBoxItem: LostAndFoundItem | null;
  setSelectedSmartBoxItem: (item: LostAndFoundItem | null) => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  apiBaseUrl: string;
  setApiBaseUrl: (url: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [activePage, setActivePage] = useState<NavigationPage>('dashboard');
  const [items, setItems] = useState<LostAndFoundItem[]>([]);
  const [stats, setStats] = useState<ItemStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isInitialLoad, setIsInitialLoad] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [awsStatus, setAwsStatus] = useState<'connected' | 'not_configured' | 'error' | 'checking'>('checking');
  const [awsStatusMessage, setAwsStatusMessage] = useState<string>('');
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [apiBaseUrl, setApiBaseUrlState] = useState<string>(api.getApiBaseUrl());

  // Modals state
  const [selectedDetailItem, setSelectedDetailItem] = useState<LostAndFoundItem | null>(null);
  const [selectedEditItem, setSelectedEditItem] = useState<LostAndFoundItem | null>(null);
  const [selectedSmartBoxItem, setSelectedSmartBoxItem] = useState<LostAndFoundItem | null>(null);

  const addToast = useCallback((type: ToastMessage['type'], message: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const updateApiBaseUrl = (url: string) => {
    api.setCustomApiBaseUrl(url);
    setApiBaseUrlState(api.getApiBaseUrl());
    addToast('info', 'API Gateway URL updated. Re-checking AWS connection...');
  };

  /**
   * Fetch all items and stats from AWS API
   */
  const refreshData = useCallback(async () => {
    const configured = api.isAwsConfigured();

    if (!configured) {
      setAwsStatus('not_configured');
      setAwsStatusMessage('VITE_API_BASE_URL is not set. Connect your AWS API Gateway to load DynamoDB records.');
      setItems([]);
      setStats(null);
      setIsLoading(false);
      setIsInitialLoad(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    setAwsStatus('checking');

    try {
      // First test connection to verify API Gateway + DynamoDB
      const conn = await api.testConnection();
      if (!conn.ok) {
        setAwsStatus('error');
        setAwsStatusMessage(conn.message);
        setError(conn.message);
        setIsLoading(false);
        setIsInitialLoad(false);
        return;
      }

      setAwsStatus('connected');
      setAwsStatusMessage(`Connected to AWS API Gateway (${conn.latencyMs}ms)`);

      // Fetch items & stats concurrently
      const [fetchedItems, fetchedStats] = await Promise.all([
        api.getItems(),
        api.getStats().catch(() => null), // fallback if stats endpoint calculation fails
      ]);

      setItems(fetchedItems || []);

      if (fetchedStats) {
        setStats(fetchedStats);
      } else {
        // Calculate stats client-side from actual items if /stats route is unavailable
        const lost = (fetchedItems || []).filter((i) => i.status === 'Lost').length;
        const found = (fetchedItems || []).filter((i) => i.status === 'Found').length;
        const returned = (fetchedItems || []).filter((i) => i.status === 'Returned').length;
        const catCounts: Record<string, number> = {};
        (fetchedItems || []).forEach((i) => {
          catCounts[i.category] = (catCounts[i.category] || 0) + 1;
        });

        setStats({
          totalItems: (fetchedItems || []).length,
          lostItems: lost,
          foundItems: found,
          returnedItems: returned,
          categoryCounts: catCounts,
        });
      }
    } catch (err: any) {
      setAwsStatus('error');
      setAwsStatusMessage(err.message || 'Failed to connect to AWS');
      setError(err.message || 'Failed to fetch items from AWS DynamoDB');
      addToast('error', err.message || 'Error communicating with AWS API');
    } finally {
      setIsLoading(false);
      setIsInitialLoad(false);
    }
  }, [addToast]);

  // Initial load
  useEffect(() => {
    refreshData();
  }, [refreshData, apiBaseUrl]);

  /**
   * Register new item
   */
  const handleCreateItem = async (input: CreateItemInput): Promise<LostAndFoundItem | null> => {
    if (!api.isAwsConfigured()) {
      addToast('error', 'AWS is not connected. Configure VITE_API_BASE_URL to save items to DynamoDB.');
      return null;
    }

    setIsLoading(true);
    try {
      const created = await api.createItem(input);
      addToast('success', `Item "${created.itemName}" registered in DynamoDB with ID ${created.itemId}!`);
      await refreshData();
      return created;
    } catch (err: any) {
      addToast('error', `Registration failed: ${err.message}`);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Update full item
   */
  const handleUpdateItem = async (itemId: string, input: UpdateItemInput): Promise<LostAndFoundItem | null> => {
    if (!api.isAwsConfigured()) {
      addToast('error', 'AWS is not connected. Cannot update DynamoDB record.');
      return null;
    }

    setIsLoading(true);
    try {
      const updated = await api.updateItem(itemId, input);
      addToast('success', `Item "${updated.itemName}" updated successfully.`);
      await refreshData();
      return updated;
    } catch (err: any) {
      addToast('error', `Update failed: ${err.message}`);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Change item status (Check In / Check Out / Mark Lost)
   */
  const handleUpdateStatus = async (
    itemId: string, 
    status: ItemStatus, 
    extra?: { checkInTime?: string; checkOutTime?: string }
  ): Promise<boolean> => {
    if (!api.isAwsConfigured()) {
      addToast('error', 'AWS is not connected. Cannot modify DynamoDB item status.');
      return false;
    }

    setIsLoading(true);
    try {
      const updated = await api.updateItemStatus(itemId, status, extra);
      const actionLabel = 
        status === 'Found' ? 'Checked in to Smart Box' : 
        status === 'Returned' ? 'Checked out / Returned to Owner' : 
        'Marked as Lost';
      addToast('success', `${updated.itemName}: ${actionLabel} successfully.`);
      await refreshData();
      return true;
    } catch (err: any) {
      addToast('error', `Status change failed: ${err.message}`);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Delete item
   */
  const handleDeleteItem = async (itemId: string): Promise<boolean> => {
    if (!api.isAwsConfigured()) {
      addToast('error', 'AWS is not connected. Cannot delete DynamoDB record.');
      return false;
    }

    setIsLoading(true);
    try {
      await api.deleteItem(itemId);
      addToast('success', `Item "${itemId}" permanently deleted from DynamoDB.`);
      if (selectedDetailItem?.itemId === itemId) {
        setSelectedDetailItem(null);
      }
      await refreshData();
      return true;
    } catch (err: any) {
      addToast('error', `Delete failed: ${err.message}`);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AppContext.Provider
      value={{
        activePage,
        setActivePage,
        items,
        stats,
        isLoading,
        isInitialLoad,
        error,
        awsStatus,
        awsStatusMessage,
        toasts,
        addToast,
        removeToast,
        refreshData,
        createItem: handleCreateItem,
        updateItem: handleUpdateItem,
        updateStatus: handleUpdateStatus,
        deleteItem: handleDeleteItem,
        selectedDetailItem,
        setSelectedDetailItem,
        selectedEditItem,
        setSelectedEditItem,
        selectedSmartBoxItem,
        setSelectedSmartBoxItem,
        searchQuery,
        setSearchQuery,
        apiBaseUrl,
        setApiBaseUrl: updateApiBaseUrl,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export function useApp(): AppContextType {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
