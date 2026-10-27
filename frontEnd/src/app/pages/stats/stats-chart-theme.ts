export function readStatsChartTheme() {
  const styles = getComputedStyle(document.documentElement);
  const color = (token: string) => styles.getPropertyValue(token).trim();

  return {
    muted: color('--text-muted'),
    border: color('--border'),
    seriesColor: (index: number) => index === 0
      ? color('--accent')
      : `hsl(${(index * 137.5 + 20) % 360} 65% ${color('--chart-series-lightness')})`,
  };
}
