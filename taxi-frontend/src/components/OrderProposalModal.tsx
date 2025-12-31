import React from 'react';

interface OrderProposalModalProps {
  order: {
    ride_id: string;
    start_x: number;
    start_y: number;

    end_x?: number; // Новое поле (может не прийти от старого бэкенда)
    end_y?: number; // Новое поле
    price?: number;

  } | null;
  onAccept: () => void;
  onDecline: () => void;
}

export const OrderProposalModal: React.FC<OrderProposalModalProps> = ({ order, onAccept, onDecline }) => {
  if (!order) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 animate-in fade-in duration-200">
      <div className="bg-white p-6 rounded-2xl shadow-2xl max-w-sm w-full mx-4 border-2 border-blue-500 transform scale-100 animate-bounce-short">
        <div className="text-center">
          <div className="text-4xl mb-4">🔔</div>
          <h3 className="text-2xl font-bold text-gray-800 mb-2">Новый заказ!</h3>
          <p className="text-gray-600 mb-6">
            Подача в точку: <span className="font-mono font-bold text-blue-600">[{order.start_x}, {order.start_y}]</span>
          </p>
          
          <div className="flex gap-3">
            <button 
              onClick={onDecline}
              className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-xl font-bold hover:bg-gray-300 transition"
            >
              Пропустить
            </button>
            <button 
              onClick={onAccept}
              className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 shadow-lg shadow-blue-500/30 transition transform active:scale-95"
            >
              Принять
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};