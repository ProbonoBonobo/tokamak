if (!window.dash_clientside) {
    window.dash_clientside = {};
}

window.dash_clientside.clientside = {
    display: function (_, targets, ...values) {
        // console.log(targets, values);
        let state = {};
        for (let i = 0; i < targets.length; i++) {
            // console.log(JSON.stringify(targets[i]));
            if (values[i] != targets[i]) {
                state[targets[i]] = values[i];
            } else {
                state[targets[i]] = 'no_update';
            }


        }
        // console.log(JSON.stringify(state));
        return state;

    }
}