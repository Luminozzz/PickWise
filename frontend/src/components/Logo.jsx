// The PickWise petal/flower mark from the mock.
export default function Logo({ className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => (
        <ellipse
          key={deg}
          cx="12"
          cy="5.5"
          rx="2.1"
          ry="4.4"
          transform={`rotate(${deg} 12 12)`}
          opacity={0.55 + (deg / 315) * 0.45}
        />
      ))}
    </svg>
  )
}