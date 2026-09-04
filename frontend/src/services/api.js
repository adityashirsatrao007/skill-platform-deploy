import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, password) => 
    api.post('/auth/login', new URLSearchParams({ username: email, password })),
  register: (userData) => api.post('/auth/register', userData),
  getMe: () => api.get('/auth/me'),
};

export const competencyAPI = {
  assess: (skills, experience) => 
    api.post('/competency/assess', { skills, experience }),
  getGaps: () => api.get('/competency/gaps'),
  getFramework: () => api.get('/competency/framework'),
  getReport: () => api.get('/competency/report'),
};

export const quizAPI = {
  generate: (data) => api.post('/quiz/generate', data),
  generateFromDocument: (formData) => 
    api.post('/quiz/generate-from-document', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  submit: (data) => api.post('/quiz/submit', data),
  getHistory: () => api.get('/quiz/history'),
  getQuiz: (id) => api.get(`/quiz/${id}`),
};

export const recommendationAPI = {
  getCourses: (data) => api.post('/recommendation/courses', data),
  getLearningPath: () => api.post('/recommendation/learning-path'),
  getBySkill: (skill, level) => 
    api.get(`/recommendation/by-skill/${skill}?current_level=${level}`),
  getActivePath: () => api.get('/recommendation/active-path'),
};

export const dashboardAPI = {
  getLearnerDashboard: () => api.get('/dashboard/learner'),
  getAdminDashboard: () => api.get('/dashboard/admin'),
  getAnalytics: () => api.get('/dashboard/analytics'),
};

export const igotAPI = {
  getCourses: (category) => 
    api.get('/igot/courses', { params: { category } }),
  enroll: (courseId) => api.post(`/igot/enroll/${courseId}`),
  getProgress: () => api.get('/igot/progress'),
  getRecommended: () => api.get('/igot/recommended'),
};

export default api;
