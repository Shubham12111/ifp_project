
if (document.getElementById('choices-button-country')) {
  
  var element = document.getElementById('choices-button-country');
  const example = new Choices(element, {});
}
if (document.getElementById('choices-button-county')) {
  
  var element = document.getElementById('choices-button-county');
  const example = new Choices(element, {});
}

if (document.getElementById('choices-button-city')) {
  
  var element = document.getElementById('choices-button-city');
  const example = new Choices(element, {});
}
if (document.getElementById('choices-button-contact_type')) {
  
  var element = document.getElementById('choices-button-contact_type');
  const example = new Choices(element, {});
}


var choicesTags = document.getElementById('choices-tags');
var color = choicesTags.dataset.color;
if (choicesTags) {
  const example = new Choices(choicesTags, {
    delimiter: ',',
    editItems: true,
    maxItemCount: 5,
    removeItemButton: true,
    addItems: true,
    classNames: {
      item: 'badge rounded-pill choices-' + color + ' me-2'
    },
    noResultsText: 'No records found',
    noChoicesText: 'No records found',
    loadingText: 'Loading...',

  });
}
