import { useState } from 'react';
import { PassengerPage } from './PassengerPage';
import { DriverPage } from './DriverPage';
import { useWebSocket } from '../hooks/useWebSocket'; // # НОВОЕ
import { useAppContext } from '../context/AppContext'; // # НОВОЕ

export const DashboardPage = () => {
  const [role, setRole] = useState<'passenger' | 'driver' | null>(null);
  const { userEmail } = useAppContext(); // # НОВОЕ
  const token = localStorage.getItem('token'); // # НОВОЕ

  // # НОВОЕ: Инициализируем WebSocket-соединение
  useWebSocket(token);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_email');
    window.location.reload();
  };

  // # (код без изменений)
  if (role === 'passenger') {
    return <PassengerPage onBack={() => setRole(null)} />;
  }
  if (role === 'driver') {
    return <DriverPage onBack={() => setRole(null)} />;
  }

  // # (код без изменений)
  return (
    <div className="min-h-screen bg-gray-100 p-6 flex flex-col items-center">
      <div className="w-full max-w-4xl flex justify-between items-center mb-12">
        <h1 className="text-2xl font-bold text-gray-800">Taxi Grid 🚕</h1>
        <div className="flex items-center gap-4">
          <span className="text-gray-600">{userEmail}</span>
          <button
            onClick={handleLogout}
            className="text-red-500 hover:text-red-700 font-semibold"
          >
            Выйти
          </button>
        </div>
      </div>

      <div className="text-center mb-10">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">Кем вы хотите быть?</h2>
        <p className="text-gray-500">Выберите режим работы приложения</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8 w-full max-w-4xl">
        <button
          onClick={() => setRole('passenger')}
          className="bg-white p-8 rounded-2xl shadow-md hover:shadow-xl transition-all hover:-translate-y-1 flex flex-col items-center group"
        >
          <div className="text-6xl mb-4 group-hover:scale-110 transition-transform">🙋‍♂️</div>
          <h3 className="text-2xl font-bold text-blue-600 mb-2">Пассажир</h3>
          <p className="text-gray-500 text-center">
            Заказать такси, выбрать маршрут и отслеживать поездку.
          </p>
        </button>

        <button
          onClick={() => setRole('driver')}
          className="bg-white p-8 rounded-2xl shadow-md hover:shadow-xl transition-all hover:-translate-y-1 flex flex-col items-center group"
        >
          <div className="text-6xl mb-4 group-hover:scale-110 transition-transform">🚖</div>
          <h3 className="text-2xl font-bold text-green-600 mb-2">Водитель</h3>
          <p className="text-gray-500 text-center">
            Выйти на линию, получать заказы и зарабатывать.
          </p>
        </button>
      </div>
    </div>
  );
};