(function(root){
  app = root.app || {};

  app.QUESTION_TYPE = {
    MULTI: 'multi',
    SINGLE: 'single'
  };

  app.QUIZ_TYPE = {
    ORDINARY: 'ordinary',
    TIME_LIMIT: 'time_limit',
    CHALLENGE: 'challenge'
  };

  app.DOWNLOAD_TIMEOUT = 3000;
  app.DOWNLOAD_TRIGGER = 30; // download more if questions are less than this value, only for time limit and challenge mode

  root.app = app;
  return app;
})(window);
