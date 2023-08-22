function initializeDataTable(tableId, dataUrl, columnsConfig) {
    if (document.getElementById(tableId)) {
        console.log("Initializing DataTable for table: " + tableId);

        fetch(dataUrl, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            }
        }).then(function (response) {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        }).then(function (data) {
            const responseData = JSON.parse(data.data); 
            
            var formattedData = {
                "draw": 1, // Set the appropriate draw value
                "recordsTotal": responseData.length,
                "recordsFiltered": responseData.length,
                "data": responseData.map(function(item) {
                    var row = [];
                    for (var columnConfig of columnsConfig) {
                        var cellContent = item.fields[columnConfig.fieldName];

                        if (columnConfig.type === 'status') {
                            cellContent = getStatusCellContent(item.fields.status, tableContext);
                        }  else if (columnConfig.type === 'actions') {
                            cellContent = generateActionButtons(item, columnConfig);
                        }
                        
                        row.push(cellContent);
                    }
                    return row;
                })
            };
            new simpleDatatables.DataTable("#" + tableId, {
                searchable: true,
                fixedHeight: false,
                perPage: 25,
                serverSide: true,
                processing: true,
                data: formattedData // Pass the formatted data
            });

        }).catch(function (error) {
            console.error("Fetch error for table " + tableId, error);
        });
    }
}

// Function to convert string to title case and replace underscores with spaces
function formatStatus(status) {
    console.log(status)
    return status.replace(/_/g, ' ').replace(/\w\S*/g, function(txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
}

// Condition function to handle status color and icon
function getStatusCellContent(status) {
    var cellContent = '';
     if (status === 'sent_for_approval') {
        cellContent = '<span class="text-success">' + formatStatus(status) + '</span>';
    } else {
        cellContent = '<span class="status-dark">' + formatStatus(status) + '</span>';
    }

    return cellContent;
}


// Function to generate link action HTML
function generateLinkAction(item, columnConfig) {
    var url = item.fields[columnConfig.urlField];
    var isDisabled = false; // Set this based on your conditions

    // Check if the action should be disabled based on status
    if (columnConfig.disableCondition === 'status' && item.fields.status === columnConfig.disableValue) {
        isDisabled = true;
    }

    var disabledAttribute = isDisabled ? 'disabled' : '';

    return '<a href="' + url + '" data-bs-toggle="tooltip" class="ms-2 data-bs-original-title="' + columnConfig.tooltip + '"' +
           ' ' + disabledAttribute + '>' +
           '<i class="' + columnConfig.iconClass + '" aria-hidden="true"></i>' +
           '</a>';
}
// Function to generate action buttons HTML
function generateActionButtons(item, columnConfig) {
    var actionsHTML = columnConfig.linkActions.map(function(action) {
        return generateLinkAction(item, action);
    }).join(' ');

    return actionsHTML;
}