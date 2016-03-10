(function(root, $, _, Backbone) {
  app = root.app || {};

  app.ApplicationView = Backbone.View.extend({
    el: $('#app_container'),
    dataRoot: '/data/',
    apiRoot: '/api/',
    initialize: function(options) {
      this.game_code = options.game_code;
      this.gameDataRoot = this.dataRoot + this.game_code + '/';
      this.quizConfig = options.config;
    },
    run: function() {
      var errorView;
      var used = parseInt(localStorage.getItem(this.game_code + '_count')) || 0,
        max = parseInt(this.quizConfig.max_chances);
      if (used > max) {
        errorView = new app.RejectionNoMoreChanceView();
      } else {
        var now = new Date(),
          start_at = new Date(this.quizConfig.start_at),
          end_at = new Date(this.quizConfig.end_at);
        if (now < start_at) {
          errorView = new app.RejectionTooEarlyView();
        } else if (now > end_at) {
          errorView = new app.RejectionTooLateView();
        }
      };
      if (errorView) {
        this.loadView(errorView);
      } else {
        this.prepareQuiz();
      }
    },
    rerun: function(){
      delete this.run_id;
      delete this.uid;
      this.run();
    },
    loadView: function(view) {
      this.view && (this.view.close ? this.view.close() : this.view.remove());
      this.view = view;
      this.$el.append(this.view.render().el);
    },
    loadStyle: function(){
      var style, quizType = this.quizConfig['type'];
      switch (quizType) {
        case app.QUIZ_TYPE.ORDINARY:
          style = 'theme1/css/main.css';
          break;
        case app.QUIZ_TYPE.TIME_LIMIT:
          style = 'theme2/css/main.css';
          break;
        case app.QUIZ_TYPE.CHALLENGE:
          style = 'theme3/css/main.css';
          break;
        default:
          throw new Error('Unknown Quiz Type');
      }
      $('head').append('<link rel="stylesheet" type="text/css" href="' + style + '"/>');
    },
    prepareQuiz: function() {
      var view = new app.WelcomeView({
        content: this.quizConfig.welcome,
        infoFields: this.quizConfig.info_fields,
        quizId: this.quizConfig.id
      });
      this.listenToOnce(view, 'startQuiz', this.gatherUserInfo);
      this.loadView(view);
    },
    gatherUserInfo: function(args){
      var params = {}, storageKey;
      if(_.size(args) > 0){
        var userinfo = JSON.stringify(_.object(args));
        var hash = mmh3(userinfo);
        var storageKey = this.game_code + '_uid_' + hash;
        var uid = localStorage.getItem(storageKey);
        if ( !uid ){
          params['hash'] = hash;
          params['userinfo'] = userinfo;
        } else {
          params['uid'] = uid;
        }
      }
      $.ajax({
        url: this.apiRoot + 'start/' + this.quizConfig.id,
        data: params,
        method: 'POST'
      }).done(_.bind(function(data){
        this.run_id = data['run_id'];
        if(!!storageKey){
          this.uid = data['uid'];
          localStorage.setItem(storageKey, data['uid']);
        }
        this.startQuiz();
      }, this));
    },
    startQuiz: function() {
      console.log(this.uid, this.run_id);
      var ViewClass, quizType = this.quizConfig['type'];
      var style = '';
      switch (quizType) {
        case app.QUIZ_TYPE.ORDINARY:
          ViewClass = app.OrdinaryQuizView;
          break;
        case app.QUIZ_TYPE.TIME_LIMIT:
          ViewClass = app.TimeLimitQuizView;
          break;
        case app.QUIZ_TYPE.CHALLENGE:
          ViewClass = app.ChallengeQuizView;
          break;
        default:
          throw new Error('Unknown Quiz Type');
      }
      var view = new ViewClass({
        config: this.quizConfig,
        gameDataRoot: this.gameDataRoot
      });
      var used = parseInt(localStorage.getItem(this.game_code + '_count')) || 0;
      localStorage.setItem(this.game_code + '_count', used + 1);
      this.listenToOnce(view, 'finishQuiz', this.finishQuiz);
      this.loadView(view);
    },
    finishQuiz: function(points) {
      console.log("结束，得到" + points + '分');
      var result = {'points': points};
      var data =  { 'score': points,'run_id': this.uid };
      if (!!this.uid) data['uid'] = this.uid
      $.ajax({
        url: this.apiRoot + 'end/' + this.quizConfig.id,
        data: data,
        method: 'POST'
      }).done(_.bind(function(data){
        console.log(data);
        result['rank'] = data['rank'];
        result['bestPoints'] = data['best_score'];
        result['bestRank'] = data['best_rank'];
        var view = new app.RankView({'result': result});
        this.listenToOnce(view, 'rerun', this.rerun);
        this.loadView(view);
      }, this));
    }
  });

  // mumurhash3 function from github.com/garycourt/murmurhash-js
  function mmh3(key, seed) {
    var remainder, bytes, h1, h1b, c1, c1b, c2, c2b, k1, i;
    remainder = key.length & 3; // key.length % 4
    bytes = key.length - remainder;
    h1 = seed;
    c1 = 0xcc9e2d51;
    c2 = 0x1b873593;
    i = 0;
    while (i < bytes) {
      k1 =
        ((key.charCodeAt(i) & 0xff)) |
        ((key.charCodeAt(++i) & 0xff) << 8) |
        ((key.charCodeAt(++i) & 0xff) << 16) |
        ((key.charCodeAt(++i) & 0xff) << 24);
      ++i;
      k1 = ((((k1 & 0xffff) * c1) + ((((k1 >>> 16) * c1) & 0xffff) << 16))) & 0xffffffff;
      k1 = (k1 << 15) | (k1 >>> 17);
      k1 = ((((k1 & 0xffff) * c2) + ((((k1 >>> 16) * c2) & 0xffff) << 16))) & 0xffffffff;
      h1 ^= k1;
      h1 = (h1 << 13) | (h1 >>> 19);
      h1b = ((((h1 & 0xffff) * 5) + ((((h1 >>> 16) * 5) & 0xffff) << 16))) & 0xffffffff;
      h1 = (((h1b & 0xffff) + 0x6b64) + ((((h1b >>> 16) + 0xe654) & 0xffff) << 16));
    }
    k1 = 0;
    switch (remainder) {
      case 3:
        k1 ^= (key.charCodeAt(i + 2) & 0xff) << 16;
      case 2:
        k1 ^= (key.charCodeAt(i + 1) & 0xff) << 8;
      case 1:
        k1 ^= (key.charCodeAt(i) & 0xff);
        k1 = (((k1 & 0xffff) * c1) + ((((k1 >>> 16) * c1) & 0xffff) << 16)) & 0xffffffff;
        k1 = (k1 << 15) | (k1 >>> 17);
        k1 = (((k1 & 0xffff) * c2) + ((((k1 >>> 16) * c2) & 0xffff) << 16)) & 0xffffffff;
        h1 ^= k1;
    }
    h1 ^= key.length;
    h1 ^= h1 >>> 16;
    h1 = (((h1 & 0xffff) * 0x85ebca6b) + ((((h1 >>> 16) * 0x85ebca6b) & 0xffff) << 16)) & 0xffffffff;
    h1 ^= h1 >>> 13;
    h1 = ((((h1 & 0xffff) * 0xc2b2ae35) + ((((h1 >>> 16) * 0xc2b2ae35) & 0xffff) << 16))) & 0xffffffff;
    h1 ^= h1 >>> 16;
    return h1 >>> 0;
  }

  root.app = app;
  return app;
})(this, $, _, Backbone);
