import React, { createContext, useState, useContext, type ReactNode } from 'react';
// Описываем тип уведомления, которое может прийти от сервера
export interface Notification {
  type: 'NEW_ORDER_PROPOSAL' | 'RIDE_STATUS_UPDATE' | 'ERROR';
  data: any;
  timestamp: number;
}

// Описываем структуру нашего глобального состояния
interface IAppContext {
  // Информация о пользователе (пока только email)
  userEmail: string | null;
  setUserEmail: (email: string | null) => void;

  // Массив для хранения входящих уведомлений
  notifications: Notification[];
  // Функция для добавления нового уведомления
  addNotification: (notification: Omit<Notification, 'timestamp'>) => void;
  // Функция для очистки уведомлений
  clearNotifications: () => void;
}

// Создаем контекст с начальным значением null
const AppContext = createContext<IAppContext | null>(null);

// Создаем провайдер - компонент, который будет "оборачивать" наше приложение
export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [userEmail, setUserEmail] = useState<string | null>(
    localStorage.getItem('user_email')
  );
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Функция для добавления уведомления в начало списка
  const addNotification = (notification: Omit<Notification, 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      timestamp: Date.now(),
    };
    // Добавляем новое уведомление, сохраняя предыдущие
    setNotifications(prev => [newNotification, ...prev]);
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  const value = {
    userEmail,
    setUserEmail,
    notifications,
    addNotification,
    clearNotifications,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Создаем кастомный хук для удобного доступа к контексту
export const useAppContext = (): IAppContext => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext должен использоваться внутри AppProvider');
  }
  return context;
};