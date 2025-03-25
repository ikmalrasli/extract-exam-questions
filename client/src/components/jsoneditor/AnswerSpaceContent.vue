<template>
  <div v-if="content.format === 'line'">
    <div v-for="index in content.lines" :key="index" class="pt-2">
      ............................................................................................................
    </div>
  </div>
  <span v-else-if="content.format === 'blank-space'">
    <div class="flex items-center justify-center h-32 block text-xl font-bold opacity-15">
      Answer space
    </div>
  </span>
  <div v-else-if="content.format === 'multiple-choice'" class="space-y-4">
    <span v-for="(option, index) in content.options" :key="index" class="flex gap-8 items-center">
      <div class="flex-none w-16 h-12 border-2 border-black"></div>
      <div class="flex flex-col inline">
        <span>{{ option.malay }}</span>
        <span><em>{{ option.english }}</em></span>
      </div>
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue';

defineProps({
  content: {
    type: Object,
    required: true
  }
})

// Calculate the number of dots based on the container width
const totalDots = computed(() => {
  console.log(window.innerWidth);
  return Math.ceil(window.innerWidth / 10); // Adjust this value based on the desired spacing
});
</script>

<style scoped>
.dot {
  display: inline-block;
  /* Allows the dot to be treated as a block element */
  width: 100%;
  /* Makes each dot take full width of its container */
  text-align: center;
  /* Centers the dot */
}
</style>