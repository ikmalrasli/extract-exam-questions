<script setup>
import AnswerSpaceContent from './AnswerSpaceContent.vue';
import DiagramContent from './DiagramContent.vue';
import TextContent from './TextContent.vue';

const props = defineProps({
  columns: {
    type: Number,
    required: true
  },
  items: {
    type: Object,
    required: true
  }
})
</script>

<template>
  <div class="flex grid items-center gap-4" :class="'grid-cols-'+props.columns">
    <div v-for="item in props.items">
      <div v-if="item.type === 'text'">
        <TextContent :content="item" />
      </div>
      <div v-if="item.type === 'diagram'">
        <DiagramContent :content="item" />
      </div>
      <div v-if="item.type === 'answer_space'">
        <AnswerSpaceContent :content="item" />
      </div>
    </div>
  </div>
</template>