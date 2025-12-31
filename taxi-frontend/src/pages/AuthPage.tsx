import { useState } from 'react';
import { api } from '../api/client'; // Импортируем наш настроенный axios

export const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false); // Чтобы блокировать кнопку во время загрузки

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLogin && password.length < 6) {
      alert("⚠️ Пароль слишком короткий!\nМинимальная длина пароля — 6 символов.");
      return; // Прерываем функцию, запрос не отправляется
    }
    setLoading(true);


    try {
      // Выбираем URL: либо вход, либо регистрация
      const url = isLogin ? '/auth/login' : '/auth/register';
      
      // Отправляем запрос на сервер
      const response = await api.post(url, {
        email: email,
        password: password
      });

      // Если успех:
      const { access_token } = response.data;
      
      // 1. Сохраняем токен в браузере
      localStorage.setItem('token', access_token);
      
      // 2. Сохраняем email (пригодится для отображения)
      localStorage.setItem('user_email', email);

      alert(`Успешно! Токен получен: ${access_token.substring(0, 10)}...`);
      console.log("Full Token:", access_token);

      
      window.location.reload(); 

    } catch (error: any) {
      console.error(error);
      // Если ошибка, показываем сообщение от сервера или общее
      const message = error.response?.data?.detail || "Ошибка соединения с сервером";
      alert(`Ошибка: ${message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md transition-all">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-blue-600 mb-2">Taxi Grid 🚕</h1>
          <p className="text-gray-500">
            {isLogin ? 'Войдите, чтобы начать поездку' : 'Создайте аккаунт за пару секунд'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div>
            <label className="block text-gray-700 text-sm font-semibold mb-2 ml-1">Email</label>
            <input
              type="email"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all bg-gray-50"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-semibold mb-2 ml-1">Пароль</label>
            <input
              type="password"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all bg-gray-50"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full text-white py-3.5 rounded-xl font-bold text-lg transition-all duration-200 ${
              loading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-500/30 active:scale-[0.98]'
            }`}
          >
            {loading ? 'Загрузка...' : (isLogin ? 'Войти в аккаунт' : 'Зарегистрироваться')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-500 text-sm">
            {isLogin ? 'Нет аккаунта?' : 'Уже есть аккаунт?'}
            <button
              onClick={() => { setIsLogin(!isLogin); setEmail(''); setPassword(''); }}
              className="ml-2 text-blue-600 font-bold hover:underline"
            >
              {isLogin ? 'Создать' : 'Войти'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};