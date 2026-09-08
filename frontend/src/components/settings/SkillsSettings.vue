<template>
  <div class="flex flex-col h-full space-y-3 py-6 w-full" data-testid="skills-settings">
    <div class="flex items-center justify-between gap-3 w-full">
      <div
        class="group rounded-[8px] overflow-hidden text-sm text-[var(--text-primary)] placeholder:text-[var(--text-disable)] h-8 flex items-center px-3 w-[200px] border border-[var(--Button-border-secondary)] bg-transparent ps-3 pe-3 py-1 gap-1.5 focus-within:border-[var(--border-input-active)] shrink-0"
      >
        <Search :size="16" class="shrink-0 text-[var(--icon-tertiary)]" />
        <input
          v-model="query"
          type="text"
          data-testid="skills-search-input"
          :placeholder="t('Search skills')"
          class="h-full min-w-1 flex-1 bg-transparent disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] outline-none"
        >
      </div>
      <div class="flex gap-2 items-center shrink-0">
        <button
          type="button"
          data-testid="skills-browse-button"
          class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors hover:opacity-90 active:opacity-80 h-8 min-w-[56px] px-3 rounded-[8px] gap-1 text-[13px] leading-[18px] outline outline-1 -outline-offset-1 hover:bg-[var(--fill-tsp-white-light)] text-[var(--text-primary)] outline-[var(--Button-border-secondary)] bg-transparent clickable shrink-0"
          @click="browseOpen = true"
        >
          {{ t('Browse Skills') }}
        </button>
        <SkillsCreateMenu />
      </div>
    </div>

    <SkillsBrowseDialog v-model:open="browseOpen" />

    <div class="flex-1">
      <div
        v-if="filtered.length === 0"
        class="h-full flex items-center justify-center"
      >
        <p class="text-[14px] font-medium text-[var(--text-primary)] text-center">
          {{ t('No skills yet') }}
        </p>
      </div>
      <div v-else class="space-y-4">
        <div v-if="officialSkills.length > 0" class="space-y-2">
          <p class="text-[13px] text-[var(--text-tertiary)]">
            {{ t('Official') }}
          </p>
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
            <SkillCard
              v-for="skill in officialSkills"
              :key="skill.id"
              :skill="skill"
            />
          </div>
        </div>
        <div v-if="personalSkills.length > 0" class="space-y-2">
          <p class="text-[13px] text-[var(--text-tertiary)]">
            {{ t('Personal') }}
          </p>
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
            <SkillCard
              v-for="skill in personalSkills"
              :key="skill.id"
              :skill="skill"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Search } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { useSkills } from '@/composables/useSkills'
import SkillCard from '@/components/skills/SkillCard.vue'
import SkillsBrowseDialog from '@/components/skills/SkillsBrowseDialog.vue'
import SkillsCreateMenu from '@/components/skills/SkillsCreateMenu.vue'

const { t } = useI18n()
const { filterByQuery } = useSkills()
const query = ref('')
const browseOpen = ref(false)

const filtered = computed(() => filterByQuery(query.value))
const officialSkills = computed(() => filtered.value.filter((s) => s.owner_type === 'official'))
const personalSkills = computed(() => filtered.value.filter((s) => s.owner_type === 'personal'))
</script>
