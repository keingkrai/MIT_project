function TeamCard({ teamKey, teamState, title, subtitle }) {
  const completed = (teamState.filter((member) => member.status === 'completed').length / teamState.length) * 100
  const percentage = Math.round(completed)
  const degrees = (percentage / 100) * 360

  return (
    <article className="team-card" data-team={teamKey}>
      <header>
        <div>
          <p>{title}</p>
          <span>{subtitle}</span>
        </div>
        <div
          className="progress-ring"
          style={{
            background: `conic-gradient(var(--accent) ${degrees}deg, rgba(255,255,255,0.08) 0deg)`,
          }}
        >
          <span>{percentage}%</span>
        </div>
      </header>
      <ul className="team-list">
        {teamState.map((member) => (
          <li key={member.name}>
            <span>{member.name}</span>
            <span className={`status-pill ${member.status}`}>
              {member.status.replace('_', ' ')}
            </span>
          </li>
        ))}
      </ul>
    </article>
  )
}

export default TeamCard

