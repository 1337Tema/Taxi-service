import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { wsService } from '../api/websocket';
import { GridMap } from '../components/GridMap';
import { OrderProposalModal } from '../components/OrderProposalModal';

export const DriverPage = ({ onBack }: { onBack: () => void }) => {
  const [isOnline, setIsOnline] = useState(false);
  const [location, setLocation] = useState({ x: 50, y: 50 });
  const [status, setStatus] = useState('offline');
  const [lastUpdate, setLastUpdate] = useState<string>('-');
  
  const [activeRide, setActiveRide] = useState<any>(null);
  const [incomingOrder, setIncomingOrder] = useState<any>(null);

  // Валидация координат
  const updateCoord = (axis: 'x' | 'y', value: string) => {
    let val = parseInt(value);
    if (isNaN(val)) val = 0;
    val = Math.max(0, Math.min(99, val));
    setLocation(prev => ({ ...prev, [axis]: val }));
  };

  useEffect(() => {
    let intervalId: any;
    const sendHeartbeat = async () => {
      try {
        await api.put('/drivers/me/presence', {
          status: 'online',
          location: { x: Number(location.x), y: Number(location.y) }
        });
        setLastUpdate(new Date().toLocaleTimeString());
        setStatus('online');
      } catch (e) { setStatus('error'); }
    };

    if (isOnline) {
      sendHeartbeat();
      intervalId = setInterval(sendHeartbeat, 3000);
      
      // WebSocket подключение
      wsService.connect();
      const unsubscribe = wsService.subscribe((msg) => {
        if (msg.type === 'NEW_ORDER_PROPOSAL') {
          console.log("🔔 Получен заказ:", msg.data);
          setIncomingOrder(msg.data);
        }
      });

      return () => {
        clearInterval(intervalId);
        unsubscribe();
        wsService.disconnect();
      };
    } else {
      setStatus('offline');
    }
  }, [isOnline, location]);

  const handleAcceptOrder = async () => {
    if (!incomingOrder) return;
    try {
      const res = await api.post(`/rides/${incomingOrder.ride_id}/accept`);
      setActiveRide(res.data);
      setIncomingOrder(null);
    } catch (e) {
      alert("Не удалось принять заказ.");
      setIncomingOrder(null);
    }
  };

  const updateRideStatus = async (newStatus: string) => {
    if (!activeRide) return;
    try {
      const res = await api.put(`/rides/${activeRide.ride_id}/status`, { status: newStatus });
      setActiveRide(res.data);
      if (newStatus === 'completed') {
        alert("Поездка завершена!");
        setActiveRide(null);
      }
    } catch (e) {
      alert("Ошибка обновления статуса");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 md:p-8">
      {/* Модалка с уведомлением */}
      <OrderProposalModal 
        order={incomingOrder}
        onAccept={handleAcceptOrder}
        onDecline={() => setIncomingOrder(null)}
      />

      <div className="max-w-7xl mx-auto flex justify-between items-center mb-6">
        <button onClick={onBack} className="bg-white px-4 py-2 rounded-lg text-gray-700">← Меню</button>
        <div className={`flex items-center gap-3 px-4 py-2 rounded-lg ${isOnline ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-600'}`}>
          <span className={`w-3 h-3 rounded-full ${isOnline ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`}></span>
          <span className="font-bold">{isOnline ? 'ВЫ НА ЛИНИИ' : 'ОФФЛАЙН'}</span>
        </div>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8 h-full">
        <div className="lg:col-span-2 bg-white p-6 rounded-3xl shadow-xl flex flex-col items-center justify-center min-h-[500px]">
          <h2 className="text-xl font-bold text-gray-800 mb-4 self-start">🗺️ Навигация по городу</h2>
          <div className="w-full h-full flex items-center justify-center p-4 bg-gray-50 rounded-2xl border border-gray-100">
            <div className="w-full max-w-2xl aspect-square">
               <GridMap 
                x={location.x} 
                y={location.y} 
                isOnline={isOnline}
                onMove={(newX, newY) => setLocation({ x: newX, y: newY })} 
                pickup={activeRide ? {x: activeRide.start_x, y: activeRide.start_y} : null}
                destination={activeRide ? {x: activeRide.end_x, y: activeRide.end_y} : null}
              />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-3xl shadow-xl h-fit sticky top-4">
          <h2 className="text-xl font-bold text-gray-800 mb-6">⚙️ Управление</h2>
          <div className="bg-blue-50 p-5 rounded-2xl mb-6 border border-blue-100">
            <label className="block text-blue-800 text-sm font-bold mb-3">ТЕКУЩИЕ КООРДИНАТЫ</label>
            <div className="flex gap-4">
              <div className="flex-1">
                <span className="text-blue-400 text-xs uppercase font-bold block mb-1">X</span>
                <input type="number" min="0" max="99" value={location.x} onChange={(e) => updateCoord('x', e.target.value)} className="w-full p-3 border border-blue-200 rounded-xl font-mono text-xl text-center outline-none" />
              </div>
              <div className="flex-1">
                <span className="text-blue-400 text-xs uppercase font-bold block mb-1">Y</span>
                <input type="number" min="0" max="99" value={location.y} onChange={(e) => updateCoord('y', e.target.value)} className="w-full p-3 border border-blue-200 rounded-xl font-mono text-xl text-center outline-none" />
              </div>
            </div>
            <p className="text-xs text-blue-400 mt-2 text-center">⚠️ Допустимый диапазон: 0 - 99</p>
          </div>

          {!isOnline ? (
            <button onClick={() => setIsOnline(true)} className="w-full py-5 rounded-2xl font-bold text-xl bg-green-600 text-white shadow-lg hover:bg-green-700">🚀 ВЫЙТИ НА ЛИНИЮ</button>
          ) : (
            <div className="space-y-6">
              {!activeRide && (
                <div className="bg-green-50 p-6 rounded-2xl border border-green-200 text-center animate-pulse">
                  <div className="text-4xl mb-2">📡</div>
                  <h3 className="font-bold text-green-800">Поиск заказов...</h3>
                  <p className="text-sm text-green-600">Ожидайте уведомления</p>
                </div>
              )}

              {activeRide && (
                <div className="bg-indigo-50 p-5 rounded-2xl border-2 border-indigo-200">
                  <div className="flex justify-between items-center mb-4 pb-4 border-b border-indigo-200">
                    <span className="font-bold text-indigo-900 text-lg">ЗАКАЗ #{activeRide.ride_id}</span>
                    <span className="text-xs bg-white text-indigo-600 px-2 py-1 rounded font-mono border border-indigo-200">{activeRide.status}</span>
                  </div>
                  <div className="space-y-3 mb-6 bg-white p-3 rounded-xl border border-indigo-100">
                    <div className="flex justify-between">
                      <span className="text-gray-500 text-sm">🙋‍♂️ Забрать:</span>
                      <span className="font-mono font-bold text-gray-800 text-lg">{activeRide.start_x}, {activeRide.start_y}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500 text-sm">🏁 Везти:</span>
                      <span className="font-mono font-bold text-gray-800 text-lg">{activeRide.end_x}, {activeRide.end_y}</span>
                    </div>
                    <div className="flex justify-between text-green-700 font-bold border-t pt-2 mt-2">
                      <span>Сумма:</span><span>{activeRide.price || activeRide.estimated_price} ₽</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-3">
                    {activeRide.status === 'driver_assigned' && <button onClick={() => updateRideStatus('driver_arrived')} className="w-full py-4 bg-purple-600 text-white rounded-xl font-bold">📍 Я приехал</button>}
                    {activeRide.status === 'driver_arrived' && <button onClick={() => updateRideStatus('passenger_onboard')} className="w-full py-4 bg-orange-500 text-white rounded-xl font-bold">🚶 Пассажир сел</button>}
                    {activeRide.status === 'passenger_onboard' && <button onClick={() => updateRideStatus('in_progress')} className="w-full py-4 bg-blue-600 text-white rounded-xl font-bold">🏁 Поехали</button>}
                    {activeRide.status === 'in_progress' && <button onClick={() => updateRideStatus('completed')} className="w-full py-4 bg-green-600 text-white rounded-xl font-bold">✅ Завершить</button>}
                  </div>
                </div>
              )}

              <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 flex justify-between text-sm">
                <span>Статус сети: <span className="text-green-600 font-bold uppercase">{status}</span></span>
                <span>Обновлено: <span className="font-mono">{lastUpdate}</span></span>
              </div>

              <button onClick={() => setIsOnline(false)} className="w-full py-4 rounded-2xl font-bold text-red-500 border-2 border-red-100 hover:bg-red-50">⛔ ЗАКОНЧИТЬ СМЕНУ</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};