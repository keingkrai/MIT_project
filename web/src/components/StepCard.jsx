function StepCard({ step, title, children }) {
  return (
    <article className="step-card" data-step={step}>
      <header>
        <p>Step {step}</p>
        <h2>{title}</h2>
      </header>
      {children}
    </article>
  )
}

export default StepCard

