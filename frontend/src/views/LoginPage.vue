<template>
  <div class="flex flex-col items-center justify-center min-h-screen gap-4">
    <h1 class="text-2xl font-bold">Login</h1>
    <input v-model="username" placeholder="Username" class="border px-4 py-2 rounded w-64" />
    <input v-model="password" type="password" placeholder="Password" class="border px-4 py-2 rounded w-64" />
    <button @click="login" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
      Login
    </button>
    <p v-if="error" class="text-red-500 mt-2">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { isAuthenticated } from '@/router/index.js'; // Import from router/index.js

const username = ref('');
const password = ref('');
const error = ref('');
const router = useRouter();

const login = async () => {
  error.value = '';
  try {
    const res = await fetch('http://127.0.0.1:5000/login', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value,
      }),
    });

    if (res.ok) {
      isAuthenticated.value = true;
      console.log('Login successful. About to push /');
      router.push('/');
    } else {
      const data = await res.json();
      username.value = '';
      password.value = '';
      console.log('Login failed:', data);
      error.value = 'Login failed. Please check your credentials.';
    }
  } catch (err) {
    console.error('Login error:', err);
    error.value = 'Network error. Please try again later.';
  }
};
</script>