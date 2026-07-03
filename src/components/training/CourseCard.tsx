import type { Course } from '../../types/training'
import { TrainingCourseCard } from './TrainingCourseCard'
export function CourseCard({course}:{course:Course}){return <TrainingCourseCard course={course}/>}
