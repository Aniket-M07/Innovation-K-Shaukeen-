function Card({ children, className = "" }) {
  return <section className={`glass-card ${className}`}>{children}</section>;
}

export default Card;