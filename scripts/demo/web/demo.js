
function getSelectValues(selectid) {
  const select = document.getElementById(selectid);
  var result = [];
  var options = select && select.options;
  console.error(options)
  if (!options) {
    return result;
  }
  var opt;

  for (var i=0, iLen=options.length; i<iLen; i++) {
    opt = options[i];

    if (opt.selected) {
      result.push(opt.value || opt.text);
    }
  }
  return result;
}

async function plot(mode="replace") {
  // get select values
  const data = {};
  const graphtypes = getSelectValues("graphtypeselect")
  data.graphtype = graphtypes.join(",")
  const sections = getSelectValues("sectionselect")
  data.section = sections.join(",")
  const events = getSelectValues("eventselect")
  data.eventtype = events.join(",")
  const counttype = getSelectValues("countselect")
  data.count = counttype.join(",")
  const response = await fetch('/plotjson?'+(new URLSearchParams(data)), {"method": "GET"});
  const res = await response.json();
  if (mode != "add")
    Plotly.purge('chart')
  Plotly.plot('chart', res, {});
}

async function resetplot() {
  Plotly.plot('chart');
}