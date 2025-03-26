<script setup>
import DiagramContent from './DiagramContent.vue';
import TextContent from './TextContent.vue';
import RowContent from './RowContent.vue';

defineProps({
  number: {
    type: String,
    required: true
  },
  content: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    required: true
  }
})
</script>

<template>
  <tr v-if="content.type === 'text'">
    <td v-if="index === 0">{{ number }}.</td>
    <td v-else></td>
    <td colspan="3">
      <TextContent :content="content" />
    </td>
  </tr>
  <tr v-if="content.type === 'diagram'">
    <td></td>
    <td colspan="3">
      <DiagramContent :content="content" />
    </td>
  </tr>
  <tr v-if="content.type === 'row'">
    <td></td>
    <td colspan="3">
      <RowContent :content="content.items" />
    </td>
  </tr>
</template>

<style scoped>
th,
td {
  border: 1px solid black;
  padding: 8px;
  vertical-align: top;
}
.checkbox {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 1px solid black;
}
</style>