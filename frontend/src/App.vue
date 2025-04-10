<template>
    <div>
        <Drawer v-model:visible="drawer" header="Settings">
            <Card>
                <template #title>Distance {{ distance }}</template>
                <template #content>
                    <Slider v-model="distance" min="5" max="50"/>
                </template>
            </Card>
            <Card>
                <template #title>Price {{ '$'.repeat(price) }}</template>
                <template #content>
                    <Slider v-model="price" min="1" max="4"/>
                </template>
            </Card>
        </Drawer>
        <div class="flex left-0 fixed bottom-8 w-screen">
            <div class="w-1/3"></div>
            <div class="xl3:w-1/3">
                    <div class="flex items-center gap-x-[5vw]">
                    <Button raised rounded @click="drawer = true"><span class="material-icons">menu</span></Button>
                    <Button raised rounded @click="drawer = true"><span class="material-icons">close</span></Button>
                    <Button raised rounded @click="drawer = true"><span class="material-icons">search</span></Button>
                    <Button raised rounded @click="drawer = true"><span class="material-icons">favorite</span></Button>
                    <Button raised rounded @click="drawer = true"><span class="material-icons">undo</span></Button>
                </div>
            </div>
            <div class="w-1/3"></div>
        </div>
    </div>
</template>

<script setup>
import Drawer from 'primevue/drawer';
import Button from 'primevue/button';
import Slider from 'primevue/slider';
import Card from 'primevue/card';
import { ref } from "vue";

const drawer = ref(false);
const distance = ref(15);
const price = ref(2);
</script>
