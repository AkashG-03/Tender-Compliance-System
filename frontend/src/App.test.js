import { render, screen } from '@testing-library/react';
import App from './App';

test('renders tender compliance system', () => {
  render(<App />);
  const titleElement = screen.getByText(/Tender Compliance System/i);
  expect(titleElement).toBeInTheDocument();
});
