import Navbar from '../components/Navbar.jsx'
import Questionnaire from '../questionnaire/Questionnaire.jsx'

export default function QuestionnairePage({ onNavigate }) {
  return (
    <>
      <Navbar onNavigate={onNavigate} />
      <Questionnaire onNavigate={onNavigate} />
    </>
  )
}
