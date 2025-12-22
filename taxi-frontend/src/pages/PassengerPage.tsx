import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { GridMap } from '../components/GridMap';

export const PassengerPage = ({ onBack }: { onBack: () => void }) => {
  const [step, setStep] = useState<'select_start' | 'select_end' | 'ready' | 'ordered' | 'completed'>('select_start');
  const [pickup, setPickup] = useState<{ x: number, y: number } | null>(null);
  const [destination, setDestination] = useState<{ x: number, y: number } | null>(null);
  const [rideInfo, setRideInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [rating, setRating] = useState(0);

  // АВТО-ОБНОВЛЕНИЕ СТАТУСА
  useEffect(() => {
    let interval: any;
    if (step === 'ordered' && rideInfo?.ride_id) {
      interval = setInterval(async () => {
        try {
          const res = await api.get('/rides/history');
          const myRides = res.data;
          // Берем последний заказ с таким же ID
          const currentRide = myRides.find((r: any) => r.ride_id === rideInfo.ride_id);
          
          if (currentRide) {
            setRideInfo(currentRide);
            if (currentRide.status === 'completed') {
              setStep('completed');
              clearInterval(interval);
            }
          }
        } catch (e) {
          console.error(e);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [step, rideInfo]);

  const handleMapClick = (x: number, y: number) => {
    if (step === 'select_start') {
      setPickup({ x, y });
      setStep('select_end');
    } else if (step === 'select_end') {
      setDestination({ x, y });
      setStep('ready');
    }
  };

  const handleOrder = async () => {
    if (!pickup || !destination) return;
    setLoading(true);
    
    // ПРЕОБРАЗУЕМ В ЧИСЛА, ЧТОБЫ ИЗБЕЖАТЬ ОШИБКИ 422
    const payload = {
      start_x: Number(pickup.x),
      start_y: Number(pickup.y),
      end_x: Number(destination.x),
      end_y: Number(destination.y)
    };

    try {
      const response = await api.post('/rides', payload);
      setRideInfo(response.data);
      setStep('ordered');
    } catch (error: any) {
      console.error(error);
      if (error.response?.status === 422) {
        alert("Ошибка валидации данных. Проверьте консоль.");
      } else {
        alert("Ошибка при создании заказа");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setPickup(null);
    setDestination(null);
    setRideInfo(null);
    setRating(0);
    setStep('select_start');
  };

  const submitRating = () => {
    alert(`Спасибо за оценку ${rating} звезд!`);
    handleReset();
  };

  const getStatusColor = (s: string) => {
    switch(s) {
      case 'pending': return 'text-orange-500';
      case 'driver_assigned': return 'text-blue-600';
      case 'driver_arrived': return 'text-purple-600';
      case 'in_progress': return 'text-green-600 animate-pulse';
      case 'completed': return 'text-gray-800';
      default: return 'text-gray-500';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 md:p-8">
      <div className="max-w-7xl mx-auto mb-6">
        <button onClick={onBack} className="bg-white px-4 py-2 rounded-lg shadow-sm hover:shadow-md text-gray-700">← Назад</button>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* КАРТА */}
        <div className="lg:col-span-2 bg-white p-6 rounded-3xl shadow-xl min-h-[500px] flex flex-col items-center">
          <h2 className="text-xl font-bold text-gray-800 mb-4 self-start">
            {step === 'select_start' && "📍 Шаг 1: Выберите точку подачи (Откуда?)"}
            {step === 'select_end' && "🏁 Шаг 2: Выберите пункт назначения (Куда?)"}
            {(step === 'ready' || step === 'ordered') && "🗺️ Маршрут построен"}
            {step === 'completed' && "🎉 Поездка завершена"}
          </h2>

          <div className="w-full max-w-2xl aspect-square">
            <GridMap pickup={pickup} destination={destination} onMove={handleMapClick} />
          </div>
        </div>

        {/* ПАНЕЛЬ */}
        <div className="bg-white p-6 rounded-3xl shadow-xl h-fit sticky top-4">
          <h2 className="text-xl font-bold text-gray-800 mb-6">🚖 Заказ такси</h2>

          {step === 'completed' ? (
            <div className="text-center py-10">
              <h3 className="text-2xl font-bold text-green-600 mb-4">Поездка завершена!</h3>
              <p className="mb-6 text-gray-600">Как вам поездка?</p>
              <div className="flex justify-center gap-2 mb-8">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button key={star} onClick={() => setRating(star)} className="text-4xl hover:scale-125 transition">
                    {star <= rating ? '⭐' : '☆'}
                  </button>
                ))}
              </div>
              <button onClick={submitRating} className="w-full bg-blue-600 text-white py-3 rounded-xl font-bold">
                Отправить оценку
              </button>
            </div>
          ) : (
            <>
              <div className="space-y-4 mb-8">
                <div className="bg-blue-50 p-4 rounded-xl border border-blue-100 relative">
                  <span className="text-xs font-bold text-blue-500 uppercase">Точка А (Откуда)</span>
                  <div className="text-lg font-mono font-bold text-gray-700">{pickup ? `${pickup.x}, ${pickup.y}` : "—"}</div>
                </div>
                <div className="bg-red-50 p-4 rounded-xl border border-red-100">
                  <span className="text-xs font-bold text-red-500 uppercase">Точка Б (Куда)</span>
                  <div className="text-lg font-mono font-bold text-gray-700">{destination ? `${destination.x}, ${destination.y}` : "—"}</div>
                </div>
              </div>

              {(pickup || destination) && !rideInfo && (
                <button onClick={handleReset} className="w-full mb-4 py-2 border-2 border-gray-200 text-gray-500 rounded-lg hover:bg-gray-100 text-sm font-bold">
                  ❌ Сбросить маршрут
                </button>
              )}

              {rideInfo && (
                <div className="mb-6 bg-gray-50 p-4 rounded-xl border-2 border-gray-200">
                  <div className="flex justify-between mb-2">
                    <span className="text-gray-600">ID заказа:</span>
                    <span className="font-mono text-xs bg-white px-1 border rounded">{rideInfo.ride_id}</span>
                  </div>
                  <div className="flex justify-between mb-2">
                    <span className="text-gray-600">Цена:</span>
                    <span className="font-bold text-xl text-green-700">{rideInfo.estimated_price} ₽</span>
                  </div>
                  <div className="flex justify-between items-center mt-4 pt-4 border-t">
                    <span className="text-gray-600 font-bold">СТАТУС:</span>
                    <span className={`font-black text-lg uppercase ${getStatusColor(rideInfo.status)}`}>
                      {rideInfo.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              )}

              {step === 'ready' && (
                <button onClick={handleOrder} disabled={loading} className="w-full py-4 bg-black text-white rounded-xl font-bold text-lg hover:bg-gray-800 transition-all shadow-lg active:scale-95 disabled:opacity-50">
                  {loading ? 'Создаем...' : '🚖 Поехали!'}
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};