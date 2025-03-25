<script setup>
defineProps({
  sections: {
    type: Array,
    required: false
  }
});
</script>

<template>
  <div class="p-6 space-y-4 text-black">
    <div v-for="questions in sections">
      <div v-if="questions" class="space-y-8 mt-4">
        <template v-for="mainQuestion in questions.main_questions" :key="mainQuestion.number">
          <div class="border p-4 rounded-md bg-white shadow-md text-left">
            <table class="w-full border-collapse border mt-2 bg-gray-50">
              <tbody>
                <template
                  v-for="(content, index) in mainQuestion.content_flow"
                  :key="content.number"
                >
                  <tr v-if="content.type === 'text'">
                    <td v-if="index === 0">{{ mainQuestion.number }}.</td>
                    <td v-else></td>
                    <td colspan="3">
                      <div>{{ content.text.malay }}</div>
                      <div class="italic">{{ content.text.english }}</div>
                    </td>
                  </tr>
                  <tr v-if="content.type === 'diagram'">
                    <td></td>
                    <td colspan="3" style="text-align: center">
                      <div class="diagram"></div>
                    </td>
                  </tr>
                  <tr v-if="content.type === 'answer_space'">
                    <td colspan="3" class="answer-space">
                      <span v-if="content.format === 'line'">
                        <div class="checkbox"></div>
                      </span>
                      <span v-else>
                        ...........................................................................................................
                      </span>
                    </td>
                  </tr>
                  <tr v-if="mainQuestion.marks">
                    <td
                      colspan="4"
                      style="text-align: right; font-weight: bold"
                    >
                      <span>[{{ mainQuestion.marks }} Markahs] \n [{{ mainQuestion.marks }} <em>{{ mainQuestion.marks > 1 ? 'Marks' : 'Mark' }}</em>]</span>
                    </td>
                  </tr>
                </template>
                <template
                  v-for="question in mainQuestion.questions"
                  :key="question.number"
                >
                  <tr class="border bg-gray-100">
                    <td></td>
                    <td class="border p-2">
                      {{ question.number.replace(/^\d+/, "") }}
                    </td>
                    <td class="border p-2" colspan="2">
                      <template
                        v-for="content in question.content_flow"
                        :key="content.number"
                      >
                        <div v-if="content.type === 'text'">
                          {{ content.text.malay }} <br />
                          <em>{{ content.text.english }}</em>
                        </div>
                        <div
                          v-if="content.type === 'diagram'"
                          class="diagram"
                        ></div>
                        <div
                          v-if="content.type === 'answer_space'"
                          class="answer-space"
                        >
                          <span v-if="content.format === 'line'">
                            <div class="checkbox"></div>
                          </span>
                          <div v-else-if="content.format === 'multiple-choice'" class="space-y-4">
                            <span v-for="(option, index) in content.options" :key="index" class="flex gap-8 items-center">
                              <div class="w-16 h-12 border-2 border-black"></div>
                              <div>
                                {{ option.malay }} <br />
                                <em>{{ option.english }}</em> <br />
                              </div>
                            </span>
                          </div>
                          <span v-else>
                            ...........................................................................................................
                          </span>
                        </div>
                      </template>
                    </td>
                  </tr>
                  <tr v-if="question.marks" class="border bg-gray-100">
                    <td></td>
                    <td></td>
                    <td colspan="2" align="right">
                      <span class="line-clamp-none">[{{ question.marks }} Markah][{{ question.marks }} <em>{{ question.marks > 1 ? 'Marks' : 'Mark' }}</em>]</span>
                    </td>
                  </tr>
                  <template
                    v-for="subQuestion in question.sub_questions"
                    :key="subQuestion.number"
                  >
                    <tr class="border">
                      <td></td>
                      <td></td>
                      <td class="border p-2 pl-8">
                        {{ subQuestion.number.match(/\([^)]*\)$/)?.[0] }}
                      </td>
                      <td class="border p-2">
                        <template
                          v-for="content in subQuestion.content_flow"
                          :key="content.number"
                        >
                          <div v-if="content.type === 'text'">
                            {{ content.text.malay }} <br />
                            <em>{{ content.text.english }}</em>
                          </div>
                          <div
                            v-if="content.type === 'diagram'"
                            class="diagram"
                          ></div>
                          <div
                            v-if="content.type === 'answer_space'"
                            class="answer-space"
                          >
                            <span v-if="content.format === 'checkbox'">
                              <div class="checkbox"></div>
                            </span>
                            <span v-else-if="content.format === 'multiple-choice'">
                              multiple choice
                            </span>
                            <span v-else>
                              ...........................................................................................................
                            </span>
                          </div>
                        </template>
                      </td>
                    </tr>
                    <tr v-if="subQuestion.marks" class="border bg-gray-100" align="right">
                      <td></td>
                      <td></td>
                      <td></td>
                      <td colspan="2">
                        <span>[{{ subQuestion.marks }} Markah]\\n[{{ subQuestion.marks }} <em>{{ subQuestion.marks > 1 ? 'Marks' : 'Mark' }}</em>]</span>
                      </td>
                    </tr>
                  </template>
                </template>
              </tbody>
            </table>
          </div>
        </template>
      </div>
    </div>

    <!-- <div class="flex space-x-2 mt-4">
      <button
        @click="exportToPDF"
        class="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Export to PDF
      </button>
    </div> -->
  </div>
</template>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
}
th,
td {
  border: 1px solid black;
  padding: 8px;
  vertical-align: top;
}
.diagram {
  display: inline-block;
  width: 400px;
  height: 200px;
  border: 1px solid black;
  background-color: lightgray;
}
.checkbox {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 1px solid black;
}
.answer-space {
  display: block;
  width: 100%;
}
</style>
