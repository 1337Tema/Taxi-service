import React from 'react';

interface GridMapProps {
  x?: number;
  y?: number;
  isOnline?: boolean;
  pickup?: { x: number, y: number } | null;
  destination?: { x: number, y: number } | null;
  onMove: (x: number, y: number) => void;
}

const LANDMARKS = [
  { name: 'Университет', x: 20, y: 20, icon: '🎓' },
  { name: 'ТЦ "Плаза"', x: 80, y: 20, icon: '🛍️' },
  { name: 'Центральный Парк', x: 50, y: 50, icon: '🌳' },
  { name: 'Ж/Д Вокзал', x: 20, y: 80, icon: '🚆' },
  { name: 'Аэропорт', x: 90, y: 90, icon: '✈️' },
];

export const GridMap: React.FC<GridMapProps> = ({ x, y, isOnline, pickup, destination, onMove }) => {
  const gridSize = 100;

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    const newX = Math.floor((clickX / rect.width) * gridSize);
    const newY = Math.floor((clickY / rect.height) * gridSize);
    onMove(Math.max(0, Math.min(gridSize - 1, newX)), Math.max(0, Math.min(gridSize - 1, newY)));
  };

  const handleLandmarkClick = (e: React.MouseEvent, lx: number, ly: number) => {
    e.stopPropagation();
    onMove(lx, ly);
  };

  return (
    <div className="w-full h-full flex flex-col items-center">
      <p className="text-sm text-gray-500 mb-2 text-center">
        Кликните по карте для выбора точки
      </p>
      
      <div 
        className="relative w-full aspect-square bg-gray-50 rounded-xl border-2 border-gray-300 cursor-crosshair shadow-inner"
        onClick={handleClick}
        style={{
          backgroundImage: 'linear-gradient(#e5e7eb 1px, transparent 1px), linear-gradient(90deg, #e5e7eb 1px, transparent 1px)',
          backgroundSize: '10% 10%' 
        }}
      >
        {/* Достопримечательности */}
        {LANDMARKS.map((place) => (
          <div
            key={place.name}
            onClick={(e) => handleLandmarkClick(e, place.x, place.y)}
            className="absolute flex flex-col items-center justify-center cursor-pointer hover:scale-110 transition-transform z-10"
            style={{ left: `${place.x}%`, top: `${place.y}%`, transform: 'translate(-50%, -50%)', width: '40px', height: '40px' }}
            title={place.name}
          >
            <div className="text-4xl filter drop-shadow-sm opacity-90">{place.icon}</div>
          </div>
        ))}

        {/* Старт */}
        {pickup && (
          <div className="absolute z-30 flex flex-col items-center pointer-events-none" style={{ left: `${pickup.x}%`, top: `${pickup.y}%`, transform: 'translate(-50%, -100%)' }}>
            <div className="text-4xl filter drop-shadow-md mb-[-5px]">🙋‍♂️</div>
            <span className="bg-blue-600 text-white text-[10px] px-1.5 py-0.5 rounded shadow font-bold">START</span>
          </div>
        )}

        {/* Финиш */}
        {destination && (
          <div className="absolute z-30 flex flex-col items-center pointer-events-none" style={{ left: `${destination.x}%`, top: `${destination.y}%`, transform: 'translate(-50%, -100%)' }}>
            <div className="text-4xl filter drop-shadow-md mb-[-5px]">🏁</div>
            <span className="bg-red-600 text-white text-[10px] px-1.5 py-0.5 rounded shadow font-bold">END</span>
          </div>
        )}

        {/* Машинка и координаты */}
        {x !== undefined && y !== undefined && (
          <div 
            className="absolute z-20 transition-all duration-700 ease-in-out flex flex-col items-center justify-center pointer-events-none"
            style={{ left: `${x}%`, top: `${y}%`, transform: 'translate(-50%, -50%)', width: '0px', height: '0px' }}
          >
            {/* Подпись координат (Над машиной) */}
            <div className="absolute bottom-[20px] bg-white border border-gray-300 px-2 py-0.5 rounded shadow-md text-xs font-mono font-bold text-gray-800 whitespace-nowrap z-50">
              x:{x}, y:{y}
            </div>

            <div className={`text-3xl ${isOnline ? 'filter drop-shadow-lg scale-110' : 'opacity-50 grayscale'}`}>🚖</div>
            
            {isOnline && <div className="absolute w-8 h-8 bg-green-500 rounded-full opacity-30 animate-ping -z-10"></div>}
          </div>
        )}
      </div>
    </div>
  );
};