var gulp = require('gulp'),
  uglify = require('gulp-uglify'),
  rename = require('gulp-rename'),
  concat = require('gulp-concat'),
  minify = require('gulp-clean-css'),
  prefix = require('gulp-autoprefixer'),
  stylus = require('gulp-stylus')
  maps = require('gulp-sourcemaps');

themes = ['theme1', 'theme2', 'theme3'];

themes.forEach(function (theme){
  gulp.task(theme, function() {
    return gulp.src('./'+ theme + '/styles/*.stylus')
      .pipe(maps.init())
        .pipe(stylus())
        .pipe(prefix({browsers: '> 1% in CN, iOS 7'}))
        // .pipe(minify())
        .pipe(concat('main.css'))
      .pipe(maps.write())
      .pipe(gulp.dest('./' + theme + '/css'));
  });
});

gulp.task('css', themes);

gulp.task('js', function() {
	return gulp.src('./scripts/*.js')
    .pipe(maps.init())
      .pipe(concat('packed.js'))
      // .pipe(uglify())
    .pipe(maps.write('./'))
    .pipe(gulp.dest('./js'));
});

gulp.task('watch', function() {
  themes.forEach(function (theme){
    gulp.watch('./'+ theme + '/styles/*.stylus', [theme]);
  });
  gulp.watch('scripts/*.js', ['js']);
})

gulp.task('default', ['css', 'js', 'watch']);
