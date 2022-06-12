

async function plot() {
  // get select values
  const response = await fetch('/plotjson', {method: "GET", body: data});
  const res = await response.json();
  Plotly.plot('chart', res, {});
}