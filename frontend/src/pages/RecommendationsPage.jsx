import Navbar from '../components/Navbar.jsx'
import Recommendations from '../questionnaire/Recommendations.jsx'

export default function RecommendationsPage({ answers, onNavigate }) {
  return (
    <>
      <Navbar onNavigate={onNavigate} />
      <Recommendations answers={answers} onNavigate={onNavigate} />
    </>
  )
}
