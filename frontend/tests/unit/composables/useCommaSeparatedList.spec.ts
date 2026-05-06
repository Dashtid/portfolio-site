import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useCommaSeparatedList } from '@/composables/useCommaSeparatedList'

interface Form {
  technologies: string[]
  responsibilities: string[]
}

const newForm = (): Form => ({ technologies: [], responsibilities: [] })

describe('useCommaSeparatedList', () => {
  it('joins the array on get', () => {
    const form = ref<Form>({ ...newForm(), technologies: ['Python', 'FastAPI'] })
    const adapter = useCommaSeparatedList(form, 'technologies')
    expect(adapter.value).toBe('Python, FastAPI')
  })

  it('returns empty string when the array is empty', () => {
    const form = ref<Form>(newForm())
    const adapter = useCommaSeparatedList(form, 'technologies')
    expect(adapter.value).toBe('')
  })

  it('parses a comma-separated string into a trimmed array', () => {
    const form = ref<Form>(newForm())
    const adapter = useCommaSeparatedList(form, 'technologies')
    adapter.value = 'Python,  FastAPI ,Docker'
    expect(form.value.technologies).toEqual(['Python', 'FastAPI', 'Docker'])
  })

  it('drops empty entries (trailing commas, double commas)', () => {
    const form = ref<Form>(newForm())
    const adapter = useCommaSeparatedList(form, 'technologies')
    adapter.value = 'A, , B,,C,'
    expect(form.value.technologies).toEqual(['A', 'B', 'C'])
  })

  it('clears the array when set to an empty string', () => {
    const form = ref<Form>({ ...newForm(), technologies: ['A', 'B'] })
    const adapter = useCommaSeparatedList(form, 'technologies')
    adapter.value = ''
    expect(form.value.technologies).toEqual([])
  })

  it('round-trips: get -> set with the same value yields the same array', () => {
    const form = ref<Form>({ ...newForm(), technologies: ['Vue', 'TypeScript'] })
    const adapter = useCommaSeparatedList(form, 'technologies')
    const text = adapter.value
    adapter.value = text
    expect(form.value.technologies).toEqual(['Vue', 'TypeScript'])
  })

  it('handles non-array values (e.g. legacy string) by returning empty', () => {
    // Cast — exercising the defensive branch.
    const form = ref({ technologies: null as unknown as string[] })
    const adapter = useCommaSeparatedList(form, 'technologies')
    expect(adapter.value).toBe('')
  })

  it('two adapters on the same form are independent', () => {
    const form = ref<Form>(newForm())
    const techs = useCommaSeparatedList(form, 'technologies')
    const resps = useCommaSeparatedList(form, 'responsibilities')

    techs.value = 'Python, Go'
    resps.value = 'design, ship'

    expect(form.value.technologies).toEqual(['Python', 'Go'])
    expect(form.value.responsibilities).toEqual(['design', 'ship'])
  })
})
