const govukPrototypeKit = require('govuk-prototype-kit')
const addFilter = govukPrototypeKit.views.addFilter

// Convert a radio option string into a GOV.UK radios item object
addFilter('radioItem', function (option, namePrefix) {
  return {
    value: option,
    text: option
  }
})

// Convert a checklist string into a GOV.UK checkboxes item object
addFilter('checklistItem', function (item, sectionId) {
  return {
    value: item,
    text: item
  }
})

// Map an array through a filter (used for radios and checkboxes)
addFilter('map', function (arr, filterName, extraArg) {
  if (!arr || !Array.isArray(arr)) return []

  if (filterName === 'radioItem') {
    return arr.map(function (option) {
      return {
        value: option,
        text: option
      }
    })
  }

  if (filterName === 'checklistItem') {
    return arr.map(function (item) {
      return {
        value: item,
        text: item
      }
    })
  }

  return arr
})
