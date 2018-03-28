/*
 * Remastered voting site
 * https://github.com/styczynski/pl-election-2000
 *
 * Piotr Styczyński @styczynski
 * MIT License
 */
(function() {
    // Provide voting data to the main script.
    var voting_data = {{ votingJSONFull | safe }};
    provideVotingData(voting_data);
})();