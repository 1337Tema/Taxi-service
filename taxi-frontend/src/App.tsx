import { useEffect, useState } from 'react';
import { AuthPage } from './pages/AuthPage';
import { DashboardPage } from './pages/DashboardPage';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // При загрузке приложения проверяем, есть ли токен в браузере
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  return (
    <>
      {isAuthenticated ? (
        <DashboardPage />
      ) : (
        // Если пользователь только что вошел, мы просто перезагружаем страницу
        // (в AuthPage мы делали reload, или можно передать функцию сюда)
        <AuthPage />
      )}
    </>
  );
}

export default App;