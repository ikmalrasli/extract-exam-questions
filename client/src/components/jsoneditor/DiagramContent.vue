<script setup>
const props = defineProps({
  content: {
    type: Object,
    required: true
  }
})

</script>

<template>
  <div class="flex flex-col items-center justify-center">
    <img v-if="content.url" :src="content.url" alt="Diagram Image" class="mt-2 max-w-3/4 h-auto" />
    <div v-else
      class="block flex flex-col max-w-lg w-full h-[200px] border border-black bg-gray-300 text-center items-center justify-center">
      <span class="block text-xl font-bold opacity-20">-Diagram not extracted-</span>
      <span class="block text-xl font-bold opacity-20">Page {{ content.page }}</span>
    </div>
    <span class="block">Rajah {{ content.number }}</span>
    <span class="block"><em>Diagram</em> {{ content.number }}</span>
  </div>
</template>