(function() {
    console.log('provide voting data');
    
    var voting_data = {{ votingJSONFull | safe }};
    provideVotingData(voting_data);
})();