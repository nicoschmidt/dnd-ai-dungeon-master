// The dice as outlines, drawn for this project in the manner of the d20 mark
// in the header: a silhouette, and the edges that make its shape readable.
const SHAPES: Record<number, string[]> = {
  4: ['M12 3 21.5 19.5h-19Z', 'M12 3v16.5'],
  6: ['M12 2.5 20.5 7.25v9.5L12 21.5 3.5 16.75v-9.5Z', 'M3.5 7.25 12 12l8.5-4.75M12 12v9.5'],
  8: ['M12 2 21 12 12 22 3 12Z', 'M3 12h18M12 2v20'],
  10: ['M12 2 21 10.5 12 22 3 10.5Z', 'M3 10.5 12 14l9-3.5M12 14v8M12 2 8 12.4M12 2l4 10.4'],
  12: [
    'M12 2.5 21.5 9.4 17.9 20.5H6.1L2.5 9.4Z',
    'M12 7 16.3 10.1 14.6 15.2H9.4L7.7 10.1Z',
    'M12 2.5V7M21.5 9.4l-5.2.7M17.9 20.5l-3.3-5.3M6.1 20.5l3.3-5.3M2.5 9.4l5.2.7',
  ],
  20: [
    'M12 2.5 20.5 7.25v9.5L12 21.5 3.5 16.75v-9.5Z',
    'M12 6.5 17 15H7Z',
    'M12 2.5v4M3.5 7.25 7 15M20.5 7.25 17 15M7 15l-3.5 1.75M17 15l3.5 1.75M7 15h10M12 21.5 7 15M12 21.5 17 15',
  ],
}

interface Props {
  sides: number
  size?: number
}

// Decorative: the button around it carries the name ("d20").
export function DiceIcon({ sides, size = 24 }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {SHAPES[sides].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  )
}
