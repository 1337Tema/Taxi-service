import React from 'react';

// Описываем, какие данные мы ожидаем получить для отображения
interface OrderProposal {
  ride_id: string;
  start_x: number;
  start_y: number;
  end_x: number;
  end_y: number;
  price: number;
}

interface ModalProps {
  proposal: OrderProposal;
  onAccept: (rideId: string) => void;
  onDecline: () => void; // Пока просто закрывает окно
}

export const OrderProposalModal: React.FC<ModalProps> = ({ proposal, onAccept, onDecline }) => {
  // Рассчитываем расстояние для информации
  const distance = Math.abs(proposal.start_x - proposal.end_x) + Math.abs(proposal.start_y - proposal.end_y);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-sm w-full animate-fade-in-up">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Новый заказ! 🚕</h2>
          <p className="text-gray-500 mb-6">Вам предложена новая поездка.</p>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-2xl p-4 space-y-3 mb-6">
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Откуда:</span>
            <span className="font-mono font-bold text-lg text-blue-600">{`${proposal.start_x}, ${proposal.start_y}`}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Куда:</span>
            <span className="font-mono font-bold text-lg text-red-600">{`${proposal.end_x}, ${proposal.end_y}`}</span>
          </div>
          <div className="flex justify-between items-center pt-3 border-t">
            <span className="text-gray-500">Расстояние:</span>
            <span className="font-bold text-gray-800">{distance} клеток</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Ваш доход:</span>
            <span className="font-bold text-2xl text-green-600">{proposal.price} ₽</span>
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <button
            onClick={() => onAccept(proposal.ride_id)}
            className="w-full py-4 bg-green-600 text-white rounded-xl font-bold text-lg hover:bg-green-700 transition-all shadow-lg"
          >
            ✅ Принять заказ
          </button>
          <button
            onClick={onDecline}
            className="w-full py-3 text-sm text-gray-500 hover:text-gray-800 transition-all"
          >
            Отклонить
          </button>
        </div>
      </div>
    </div>
  );
};